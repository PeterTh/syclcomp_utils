
import json
from pickle import FALSE
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
RANGE_DIMENSIONS = [i for i in range(1, MAX_DIMENSIONS+1)]
RANGE_LOOPNESTS = [i for i in range(1, MAX_LOOPNESTS+1)]
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

NEED_INT_LABELS = ["kernel_num", "buffer_num",
                   "capture_num", "dimensions", "loopnests"]

NEED_Log_Y = ["kernel_num", "buffer_num"]

USE_MARKERS = ["kernel_num", "mix", "buffer_num"]
MARKERS = [".", "v", "1", "s", "+", "d"]

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
    return json.loads(dict_str)


VALS_DONE = False


def get_times(times, vals, metrics, desired_implementation, version, exp, val):
    if exp in NEED_INT_LABELS:
        str_val = str(val)
        val = int(val)
    else:
        str_val = val
    times[val] = []
    if not VALS_DONE:
        # print(val)
        vals.append(val)
    for iteration in metrics.get(desired_implementation).get(version).get(exp).get(str_val):
        time = metrics.get(desired_implementation).get(
            version).get(exp).get(str_val).get(iteration)

        times[val].append(time)
    return times, vals


desired_experiment = sys.argv[2]
desired_value = ""
specified_value = False
int_labels = False
if desired_experiment not in SINGLE_PARAM_EXPERIMENTS.keys():
    print(
        f"Second argument must be one of {[e for e in SINGLE_PARAM_EXPERIMENTS.keys()]}")
    exit()

if desired_experiment in NEED_INT_LABELS:
    int_labels = True


f = open(sys.argv[1], "r")
hsh = f.read()
metrics = convert_hash_to_dict(hsh)

versions = {}
times = {}
vals = []
for impl in LASTS_VERSION.keys():
    version = LASTS_VERSION[impl]
    exp = desired_experiment
    for val in SINGLE_PARAM_EXPERIMENTS[exp]:
        times, vals = get_times(times, vals, metrics,
                                impl, version, exp, val)
    VALS_DONE = True
    versions[impl] = collections.OrderedDict(sorted(times.items()))

if int_labels:
    vals.sort()

for i in range(len(vals)):
    if (vals[i] == SINGLE_PARAM_EXPERIMENTS['mix'][-1]):
        vals[i] = f"mix{MIX_NUM}"
        break

data_s = {}
colors = []
c = 0
w = 0.15  # box with
offset = w*1.8  # experiment spacing
plots = []
fig, ax = plt.subplots()
lv = len(versions.keys())
ofst = [(0-lv/10.)]*len(vals)
if desired_experiment in USE_MARKERS:
    for ver in versions.keys():
        for value in versions[ver].keys():
            measures = len(versions[ver][value])
            avg = 0.0
            for time in versions[ver][value]:
                avg += time
            versions[ver][value] = avg/measures

for version in versions.keys():
    data_s[version] = []
    for val in versions[version]:
        data_s[version].append(versions[version][val])

for v in versions.keys():
    color = get_colour()
    colors.append(color)
    pos = np.array(range(len(vals)))*2+offset*c+ofst
    if desired_experiment in USE_MARKERS:
        plots.append(
            ax.plot(pos, data_s[v], color=color, marker=MARKERS[c], linestyle="None"))
        ax.plot([], c=color, label=v, marker=MARKERS[c])
    else:
        plots.append(ax.boxplot(data_s[v], positions=pos, widths=w))
        set_box_color(plots[-1], color)
        ax.plot([], c=color, label=v)
    c += 1


plt.legend()

title = ""
if specified_value:
    title = f"{desired_experiment}_{desired_value}"
else:
    title = f"{desired_experiment}"


plt.xticks(range(0, len(vals)*2, 2), vals)
ax.set_xlabel(X_LABELS[desired_experiment])
ax.set_ylabel('Time(s)')
if (desired_experiment in NEED_Log_Y):
    ax.set_yscale('log')
ax.set_title(title)

plt.savefig(f"{title}.pdf")
plt.savefig(f"{title}.png")
