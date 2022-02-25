
import json
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

X_LABELS = {"kernel_num": "Number of Kernels",
            "buffer_num": "Number of Buffers",
            "capture_num": "Number of Captures",
            "dimensions": "Buffer Dimensions ",
            "loopnests": "Number of Nested Loops",
            "type": "Data Type",
            "mix": "Type and Amount of Operations"}


REPEATS = 50
MAX_POW = 10
MAX_DIMENSIONS = 3
MAX_LOOPNESTS = 6
RANGE_MAX_POW = [2**i for i in range(MAX_POW)]
RANGE_DIMENSIONS = [i+1 for i in range(MAX_DIMENSIONS)]
RANGE_LOOPNESTS = [i+1 for i in range(MAX_LOOPNESTS)]
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


class Parameters:
    metrics_file = ""
    desired_implementation = ""
    specified_implementation = False
    desired_version = ""
    specified_version = False
    desired_experiment = ""
    specified_experiment = False
    desired_value = ""
    specified_value = False
    implementation_tags_done = False
    int_labels = False


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


def browse_values(times, p):
    if p.int_labels:
        val = str(p.desired_value)
    else:
        val = p.desired_value
    for iteration in metrics.get(impl).get(p.desired_version).get(p.desired_experiment).get(val):
        time = metrics.get(impl).get(p.desired_version).get(
            p.desired_experiment).get(val).get(iteration)
        times[impl].append(time)
    return times


p = Parameters()

p.desired_experiment = sys.argv[2]
if p.desired_experiment not in SINGLE_PARAM_EXPERIMENTS.keys():
    print(
        f"First argument must be one of {[e for e in SINGLE_PARAM_EXPERIMENTS.keys()]}")
    exit()
if (len(sys.argv) > 3):
    p.desired_value = sys.argv[4]
    specified_value = True
    if p.desired_value not in SINGLE_PARAM_EXPERIMENTS[p.desired_experiment]:
        print(
            f"{p.desired_value}  vs {SINGLE_PARAM_EXPERIMENTS[p.desired_experiment]}")
        print(
            f"Second argument must be one of {[i for i in SINGLE_PARAM_EXPERIMENTS[p.desired_experiment]]} not {p.desired_value}")
        exit()
if p.desired_experiment in NEED_INT_LABELS:
    p.int_labels = True
    if p.specified_value:
        p.desired_value = int(p.desired_value)

f = open(sys.argv[1], "r")
hsh = f.read()
metrics = convert_hash_to_dict(hsh)

implementation_times = {}
times = {}
implementation_tags = []
for impl in IMPLEMENTATION_VERSIONS.keys():
    p.desired_version = LASTS_VERSION.get(impl)
    times[impl] = []
    implementation_tags.append(impl)
    if p.specified_value:
        times = browse_values(times, p)
    else:
        for val in SINGLE_PARAM_EXPERIMENTS[p.desired_experiment]:
            p.desired_value = val
            times = browse_values(times, p)

colors = []
c = 0
w = 0.15  # box with
offset = w*1.5  # experiment spacing
plots = []
fig, ax = plt.subplots()

for v in implementation_times.keys():
    plots.append(ax.boxplot(
        [implementation_times[v]], positions=[c], sym='', widths=w))
    color = get_colour()
    set_box_color(plots[-1], color)
    colors.append(color)
    ax.plot([], c=color, label=implementation_tags[c])
    c += 1

plt.xticks(range(0, len(implementation_tags)), implementation_tags)

title = ""
if p.specified_value:
    title = f"{p.desired_experiment}_{p.desired_value}"
else:
    title = f"{p.desired_experiment}"

if (p.desired_experiment == "kernel_num"):
    ax.set_yscale('log')

ax.set_title(title)
ax.set_xlabel('Implementations')
ax.set_ylabel('Time(s)')

plt.savefig(f"{title}.pdf")
