
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
MAX_DIMENSIONS = 3+1
MAX_LOOPNESTS = 6+1
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

NEED_INT_LABELS = ["kernel_num", "buffer_num",
                   "capture_num", "dimensions", "loopnests"]

NEED_Log_Y = ["kernel_num", "buffer_num"]

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


def get_times(times, vals, metrics, desired_implementation, version, exp, val, vals_done):
    if exp in NEED_INT_LABELS:
        str_val = str(val)
        val = int(val)
    else:
        str_val = val
    times[val] = []
    if not vals_done:
        vals.append(val)
    for iteration in metrics.get(desired_implementation).get(version).get(exp).get(str_val):
        time = metrics.get(desired_implementation).get(
            version).get(exp).get(str_val).get(iteration)

        times[val].append(time)
    return times, vals


desired_implementation = sys.argv[1]
desired_experiment = sys.argv[2]
desired_value = ""
specified_value = False
if desired_implementation not in IMPLEMENTATION_VERSIONS.keys():
    print(
        f"First argument must be one of {[i for i in IMPLEMENTATION_VERSIONS.keys()]}")
    exit()
if desired_experiment not in SINGLE_PARAM_EXPERIMENTS.keys():
    print(
        f"Second argument must be one of {[e for e in SINGLE_PARAM_EXPERIMENTS.keys()]}")
    exit()

if len(sys.argv) == 5:
    if desired_experiment in NEED_INT_LABELS:
        # here it's needed as an int to check against the dicts
        desired_value = int(sys.argv[3])
    else:
        desired_value = sys.argv[3]

    if desired_value not in SINGLE_PARAM_EXPERIMENTS[desired_experiment]:
        print(
            f"Third argument is optional but it must be a value of the experiment specified on the 2nd argument:")
        for key in SINGLE_PARAM_EXPERIMENTS.keys():
            print(f"- {key}: {SINGLE_PARAM_EXPERIMENTS[key]}")
        exit()
    else:
        specified_value = True


metrics_value_input_order = 3
if specified_value:
    metrics_value_input_order += 1

f = open(sys.argv[metrics_value_input_order], "r")
hsh = f.read()
metrics = convert_hash_to_dict(hsh)

versions = {}
times = {}
vals = []
vals_done = False
for version in metrics.get(desired_implementation):
    exp = desired_experiment
    if specified_value:
        val = desired_value
        times, vals = get_times(times, vals, metrics,
                                desired_implementation, version, exp, val, vals_done)
    else:
        for val in SINGLE_PARAM_EXPERIMENTS[exp]:
            times, vals = get_times(times, vals, metrics,
                                    desired_implementation, version, exp, val, vals_done)

    vals_done = True
    versions[version] = collections.OrderedDict(sorted(times.items()))

if desired_experiment in NEED_INT_LABELS:
    vals.sort()

data_s = {}
for version in versions.keys():
    data_s[version] = []
    for val in versions[version]:
        data_s[version].append(versions[version][val])

for i in range(len(vals)):
    if (vals[i] == SINGLE_PARAM_EXPERIMENTS['mix'][-1]):
        vals[i] = f"mix{MIX_NUM}"
        break

colors = []
c = 0
w = 0.15  # box with
offset = w*1.5  # experiment spacing
plots = []
fig, ax = plt.subplots()
lv = len(versions.keys())
ofst = [(0-lv/10.)]*len(vals)
for v in versions.keys():
    pos = np.array(range(len(vals)))+offset*c+ofst
    plots.append(ax.boxplot(data_s[v], positions=pos, widths=w))
    color = get_colour()
    set_box_color(plots[-1], color)
    colors.append(color)
    c += 1
    ax.plot([], c=color, label=v)


plt.legend()

title = ""
if specified_value:
    title = f"{desired_implementation}_{desired_experiment}_{desired_value}"
else:
    title = f"{desired_implementation}_{desired_experiment}"

ax.set_title(title)
plt.xticks(range(0, len(vals)), vals)
ax.set_xlabel(X_LABELS[desired_experiment])
ax.set_ylabel('Time(s)')

if (desired_experiment in NEED_Log_Y):
    ax.set_yscale('log')

plt.savefig(f"{title}.pdf")
plt.savefig(f"{title}.png")
