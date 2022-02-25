# to run: python3 release_metrics debug_metrics implementation_name experiment_name [experiment_value]
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
RANGE_DIMENSIONS = [i+1 for i in range(MAX_DIMENSIONS)]
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

X_LABELS = {"kernel_num": "Number of Kernels",
            "buffer_num": "Number of Buffers",
            "capture_num": "Number of Captures",
            "dimensions": "Buffer Dimensions ",
            "loopnests": "Number of Nested Loops",
            "type": "Data Type",
            "mix": "Type and Amount of Operations"}


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
    release_file = ""
    debug_file = ""
    desired_implementation = ""
    specified_implementation = False
    desired_experiment = ""
    specified_experiment = False
    desired_value = ""
    specified_value = False
    vals_done = False
    int_labels = False


def get_times(times, vals, metrics, version, p):
    if p.int_labels:
        val = int(p.desired_value)
        str_val = str(p.desired_value)
    else:
        val = p.desired_value
        str_val = str(p.desired_value)

    times[val] = []
    if not p.vals_done:
        vals.append(val)
    for iteration in metrics.get(p.desired_implementation).get(version).get(p.desired_experiment).get(str_val):
        time = metrics.get(p.desired_implementation).get(
            version).get(p.desired_experiment).get(str_val).get(iteration)
        times[val].append(time)
    return times, vals


def browse_values(p, times, vals, metrics, version):
    if p.specified_value:
        times, vals = get_times(times, vals, metrics, version, p)
    else:
        for val in metrics.get(p.desired_implementation).get(version).get(p.desired_experiment):
            p.desired_value = val
            times, vals = get_times(times, vals, metrics, version, p)
    return times, vals


def browse_versions(metrics, p, versions, vals):
    times = {}
    for version in metrics.get(p.desired_implementation):
        versions[version] = {}
        if p.specified_experiment:
            experiment = p.desired_experiment
            times, vals = browse_values(p, times, vals, metrics, version)
        else:
            for experiment in metrics.get(p.desired_implementation).get(version):
                p.desired_experiment = experiment
                times, vals = browse_values(p, times, vals, metrics, version)
        p.vals_done = True
        versions[version] = collections.OrderedDict(sorted(times.items()))
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
    return sys.argv[1], sys.argv[2]


def assign_implementation():
    return sys.argv[3], True


def assign_experiment():
    return sys.argv[4], True


def assign_value():
    return sys.argv[5], True


p = Parameters()

len_args = len(sys.argv)
if len_args > 6:
    print("Wrong number of arguments.")
    exit()
if len_args > 2:
    p.release_file, p.debug_file = assign_metrics_paths()
if len_args > 3:
    p.desired_implementation, p.specified_implementation = assign_implementation()
if len_args > 4:
    p.desired_experiment, p.specified_experiment = assign_experiment()
if len_args > 5:
    p.desired_value, p.specified_value = assign_value()
if len_args < 4:
    print(f"You must specify implementation and experiment, otherwise there is too much data.")


if p.specified_implementation and p.desired_implementation not in IMPLEMENTATION_VERSIONS.keys():
    print(
        f"3rd argument must be one of {[i for i in IMPLEMENTATION_VERSIONS.keys()]}")
    exit()
if p.specified_experiment and p.desired_experiment not in SINGLE_PARAM_EXPERIMENTS.keys():
    print(
        f"4th argument must be one of {[e for e in SINGLE_PARAM_EXPERIMENTS.keys()]}")
    exit()
if p.desired_experiment in NEED_INT_LABELS:
    p.int_labels = True

if p.specified_value:
    if p.int_labels:
        p.desired_value = int(p.desired_value)
    if p.desired_value not in SINGLE_PARAM_EXPERIMENTS[p.desired_experiment]:
        print(
            f"5th argument must be one of {[e for e in SINGLE_PARAM_EXPERIMENTS[p.desired_experiment]]} for {p.desired_experiment}")
        exit()

print(f"{p.release_file} {p.debug_file} {p.desired_implementation} {p.specified_implementation} {p.desired_experiment} {p.specified_experiment} {p.desired_value} {p.specified_value}")

rel_file = open(p.release_file, "r")
rel_hash = rel_file.read()
rel_metrics = convert_hash_to_dict(rel_hash)

deb_file = open(p.debug_file, "r")
deb_hash = deb_file.read()
deb_metrics = convert_hash_to_dict(deb_hash)

rel_vals, rel_versions = browse_impls(rel_metrics, p)
deb_vals, deb_versions = browse_impls(deb_metrics, p)

# rel_vals and deb_vals are the same list.
vals = rel_vals
if p.int_labels:
    vals.sort()

data_s = {}
for version in rel_versions.keys():
    data_s[f"{version}_r"] = []
    data_s[f"{version}_d"] = []
    for val in rel_versions[version]:
        data_s[f"{version}_r"].append(rel_versions[version][val])
        data_s[f"{version}_d"].append(deb_versions[version][val])


ls = []
for i in range(len(vals)):
    if (vals[i] == SINGLE_PARAM_EXPERIMENTS['mix'][-1]):
        vals[i] = f"mix{MIX_NUM}"
    ls.append(str(vals[i]))

colors = []
c = 0
w = 0.15  # box with
offset = w*1.5  # experiment spacing
plots = []
fig, ax = plt.subplots()

lv = len(rel_versions.keys())
ofst = [(0-lv/5.)]*len(vals)
for v in data_s.keys():
    pos = np.array(range(len(vals)))*2+offset*c+ofst
    plots.append(ax.boxplot(data_s[v], positions=pos, sym='', widths=w))
    color = get_colour()
    set_box_color(plots[-1], color)
    colors.append(color)
    c += 1
    if (v[0] == "_"):
        v = "t"+v
    ax.plot([], c=color, label=v)


plt.legend()
plt.xticks(range(0, len(ls) * 2, 2), ls)


title = ""
if p.specified_value:
    title = f"rel_deb_{p.desired_implementation}_{p.desired_experiment}_{p.desired_value}"
else:
    title = f"rel_deb_{p.desired_implementation}_{p.desired_experiment}"

ax.set_title(title)
ax.set_xlabel(X_LABELS[p.desired_experiment])
ax.set_ylabel('Time(s)')

plt.savefig(f"{title}.pdf")
