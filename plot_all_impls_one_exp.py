import sys
import subprocess

IMPLEMENTATION_VERSIONS = {
    "ccpp": ["2_4", "2_5", "2_6", "2_7", "2_8"],
    "dpcpp_s": ["2022-01-13", "2021-11-14", "2021-09-15"],
    "dpcpp_n": ["2022-01-13", "2021-11-14", "2021-09-15"],
    "dpcpp_ns": ["2022-01-13", "2021-11-14", "2021-09-15"],
    "hipSYCL": ["2021-03-19", "2021-05-18", "2021-07-17", "2021-09-15", "2022-01-13"],
    "triSYCL": [""]
}

REPEATS = 50
MAX_POW = 10
MAX_DIMENSIONS = 3
MAX_LOOPNESTS = 6
RANGE_MAX_POW = [str(2**i) for i in range(MAX_POW)]
RANGE_DIMENSIONS = [str(i) for i in range(MAX_DIMENSIONS)]
RANGE_LOOPNESTS = [str(i) for i in range(MAX_LOOPNESTS)]
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

METRICS = "../../release50"
SCRIPT = "../../plot_exp_val.py"

# python3 plot_exp_val.py kernel_num 512 release_metrics
for exp in EXPERIMENTS:
    print(
        f"python3 {SCRIPT} {METRICS} {exp} ")  # {EXPERIMENTS[exp]}
    subprocess.run(
        ["python3", SCRIPT, METRICS, exp])  # , str(EXPERIMENTS[exp])
