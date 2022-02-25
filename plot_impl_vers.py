
import json
from operator import length_hint
from pickle import FALSE
from platform import release
import numpy as np
import matplotlib.pyplot as plt
import collections
import random
import sys

IMPLEMENTATION_VERSIONS = {
    "ccpp": ["2_4", "2_5", "2_6", "2_7", "2_8"],
    "dpcpp_s": ["2021-09-15", "2021-11-14", "2022-01-13"],
    "dpcpp_n": ["2021-09-15", "2021-11-14", "2022-01-13"],
    "dpcpp_ns": ["2021-09-15", "2021-11-14", "2022-01-13"],
    "hipSYCL": ["2021-03-19", "2021-05-18", "2021-07-17", "2021-09-15", "2022-01-13"],
    "triSYCL": [""]
}

LASTS_VERSION = {
    "ccpp": "2_8",
    "dpcpp_s": "2022-01-13",
    "dpcpp_n": "2022-01-13",
    "dpcpp_ns": "2022-01-13",
    "hipSYCL": "2022-01-13",
    "triSYCL": ""
}

REPEATS = 50
MAX_POW = 10
MAX_DIMENSIONS = 3
MAX_LOOPNESTS = 6
RANGE_MAX_POW = [2**i for i in range(MAX_POW)]
RANGE_DIMENSIONS = [i for i in range(1, MAX_DIMENSIONS)]
RANGE_LOOPNESTS = [i for i in range(1, MAX_LOOPNESTS)]
BASELINE_K = 100
MIX_NUM = 25

SINGLE_PARAM_EXPERIMENTS = {
    "kernel_num":  RANGE_MAX_POW,
    "buffer_num":  RANGE_MAX_POW,
    "capture_num":  RANGE_MAX_POW,
    "dimensions": RANGE_DIMENSIONS,
    "loopnests": RANGE_LOOPNESTS,
    "type": ["int", "float", "double"],
    "mix": [f"add{MIX_NUM*4}", f"mad{MIX_NUM*4}", f"cos{MIX_NUM*4}", f"sqrt{MIX_NUM*4}",
            f"m{MIX_NUM*2}c{MIX_NUM*2}", f"a{MIX_NUM}m{MIX_NUM}c{MIX_NUM}s{MIX_NUM}"]
}

EXPERIMENTS = {"kernel_num": RANGE_MAX_POW[-1], "buffer_num": RANGE_MAX_POW[-1],
               "capture_num": RANGE_MAX_POW[-1], "dimensions": MAX_DIMENSIONS,
               "loopnests": MAX_LOOPNESTS, "type": SINGLE_PARAM_EXPERIMENTS["type"][-1],
               "mix": SINGLE_PARAM_EXPERIMENTS["mix"][-1]}

NEED_INT_LABELS = ["kernel_num", "buffer_num",
                   "capture_num", "dimensions", "loopnests"]


def get_colour():
    hexadecimal = [
        "#"+''.join([random.choice('ABCDEF0123456789') for i in range(6)])]
    return str(hexadecimal[0])


def set_box_color(bp, color):
    plt.setp(bp['boxes'], color=color)
    plt.setp(bp['whiskers'], color=color)
    plt.setp(bp['caps'], color=color)
    plt.setp(bp['medians'], color=color)


def convert_hash_to_dict(ruby_hash):
    # replace experiments names to avoid format conflicts
    dict_str = ruby_hash.replace('add:', 'add')
    dict_str = dict_str.replace('mad:', 'mad')
    dict_str = dict_str.replace('cos:', 'cos')
    dict_str = dict_str.replace('sqrt:', 'sqrt')

    dict_str = dict_str.replace(',mad', 'mad')
    dict_str = dict_str.replace(',cos', 'cos')
    dict_str = dict_str.replace(',sqrt', 'sqrt')
    dict_str = dict_str.replace(
        f'mad{MIX_NUM*2}cos{MIX_NUM*2}', f'm{MIX_NUM*2}c{MIX_NUM*2}')
    dict_str = dict_str.replace(
        f"add{MIX_NUM}mad{MIX_NUM}cos{MIX_NUM}sqrt{MIX_NUM}", f"a{MIX_NUM}m{MIX_NUM}c{MIX_NUM}s{MIX_NUM}")

    dict_str = dict_str.replace("\"dpcpp\"", "\"dpcpp_n\"")
    dict_str = dict_str.replace("\"dpcpp_intel\"", "\"dpcpp_s\"")
    dict_str = dict_str.replace("\"dpcpp_multi\"", "\"dpcpp_ns\"")

    # Remove the ruby object key prefix
    dict_str = dict_str.replace(":", '"')
    # swap the k => v notation, and close any unshut quotes
    dict_str = dict_str.replace("=>", '" : ')
    # strip back any double quotes we created to sinlges
    dict_str = dict_str.replace('""', '"')
    dict_str = dict_str[:-11] + dict_str[-1]
    return json.loads(dict_str)  # ast.literal_eval(dict_str)#


class Parameters:
    metrics_file = ""
    desired_implementation = ""
    specified_implementation = False
    desired_version = ""
    specified_version = False
    desired_experiment = ""
    specified_experiment = False
    desired_value = ""
    specified_value = True
    vals_done = False
    int_labels = False


def get_times(times, vals, metrics, p):
    val = p.desired_value
    times[p.desired_experiment] = []
    if not p.vals_done:
        vals.append(p.desired_experiment)
    for iteration in metrics.get(p.desired_implementation).get(p.desired_version).get(p.desired_experiment).get(val):
        time = metrics.get(p.desired_implementation).get(
            p.desired_version).get(p.desired_experiment).get(val).get(iteration)
        times[p.desired_experiment].append(time)
    return times, vals


def browse_values(p, times, vals, metrics):
    p.desired_value = str(EXPERIMENTS[p.desired_experiment])
    times, vals = get_times(times, vals, metrics, p)
    return times, vals


def browse_experiments(metrics, p, times, vals):
    if p.specified_experiment:
        times, vals = browse_values(
            p, times, vals, metrics)
    else:
        for experiment in metrics.get(p.desired_implementation).get(p.desired_version):
            p.desired_experiment = experiment
            times, vals = browse_values(
                p, times, vals, metrics)
    return times, vals


def browse_versions(metrics, p, versions, vals):
    times = {}
    if p.specified_version:
        version = p.desired_version
        times, vals = browse_experiments(metrics, p, times, vals)
        p.vals_done = True
        versions[version] = times
    else:
        for version in metrics.get(p.desired_implementation):
            times = {}
            versions[version] = {}
            p.desired_version = version
            times, vals = browse_experiments(metrics, p, times, vals)
            p.vals_done = True
            versions[version] = times
    return vals, versions


def browse_impls(metrics, p):
    versions = {}
    vals = []

    if p.specified_implementation:
        vals, versions = browse_versions(
            metrics, p, versions, vals)
    else:
        for impl in IMPLEMENTATION_VERSIONS.keys():
            p.desired_implementation = impl
            vals, versions = browse_versions(
                metrics, p, versions, vals)
    return vals, versions


def assign_metrics_paths():
    return sys.argv[1]


def assign_implementation():
    return sys.argv[2], True


def assign_version():
    return sys.argv[3], True


p = Parameters()

len_args = len(sys.argv)
if len_args > 4:
    print("Wrong number of arguments.")
    exit()
else:
    p.metrics_file = assign_metrics_paths()
if len_args > 2:
    p.desired_implementation, p.specified_implementation = assign_implementation()
if len_args > 3:
    p.desired_version, p.specified_version = assign_version()


if p.specified_implementation and p.desired_implementation not in IMPLEMENTATION_VERSIONS.keys():
    print(
        f"3rd argument must be one of {[i for i in IMPLEMENTATION_VERSIONS.keys()]}")
    exit()
if p.specified_version and p.desired_version not in IMPLEMENTATION_VERSIONS[p.desired_implementation]:
    print(
        f"4th argument must be one of {[e for e in SINGLE_PARAM_EXPERIMENTS[p.desired_implementation]]}")
    exit()

print(f"{p.metrics_file} {p.desired_implementation} {p.specified_implementation} {p.desired_version} {p.specified_version}")

hash = open(p.metrics_file, "r").read()
metrics = convert_hash_to_dict(hash)
vals, versions = browse_impls(metrics, p)
data_s = {}
for version in versions.keys():
    data_s[version] = []
    for val in versions[version]:
        data_s[version].append(versions[version][val])


ls = []
for v in vals:
    ls.append(str(v))

w = 0.15  # box with
offset = w*1.5  # experiment spacing
colors = []
c = 0
plots = []
fig, ax = plt.subplots()
lv = len(versions.keys())
ofst = [(0-lv/10.)]*len(vals)
for v in data_s.keys():
    pos = np.array(range(len(vals)))*2+offset*c+ofst
    plots.append(ax.boxplot(data_s[v], positions=pos, sym='', widths=w))
    color = get_colour()
    set_box_color(plots[-1], color)
    colors.append(color)
    c += 1
    ax.plot([], c=color, label=v)

plt.legend()
plt.xticks(range(0, len(ls) * 2, 2), ls, fontsize=7)

title = ""
if p.specified_version:
    title = f"all_experiments_{p.desired_implementation}_{p.desired_version}"
else:
    title = f"all_experiments_{p.desired_implementation}"

ax.set_title(title)
ax.set_xlabel('Experiments')
ax.set_ylabel('Time(s)')

NEED_Log_Y = ["kernel_num", "buffer_num"]
if (p.desired_experiment in NEED_Log_Y):
    ax.set_yscale('log')

plt.savefig(f"{title}.pdf")
plt.savefig(f"{title}.png")
