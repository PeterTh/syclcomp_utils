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

MIX_NUM = 25

EXPERIMENTS = {"kernel_num": "512", "buffer_num": "512",
               "capture_num": "512", "dimensions": "3", "loopnests": "3", "type": "double", "mix": f"a{MIX_NUM}m{MIX_NUM}c{MIX_NUM}s{MIX_NUM}"}

REL = "../../release50"
DEB = "../../debug50"
SCRIPT = "../../plot_exp_rel_deb.py"

# python3 plot_exp_rel_deb.py release_metrics debug_metrics implementation_name experiment_name [experiment_value]
for impl in IMPLEMENTATION_VERSIONS:
    for exp in EXPERIMENTS:
        # {EXPERIMENTS[exp]}
        print(f"python3 {SCRIPT} {REL} {DEB} {impl} {exp}")
        subprocess.run(["python3", SCRIPT, REL, DEB, impl, exp])
        val = EXPERIMENTS[exp]
        print(
            f"python3 {SCRIPT} {REL} {DEB} {impl} {exp} {val}")  # {EXPERIMENTS[exp]}
        subprocess.run(
            ["python3", SCRIPT, REL, DEB, impl, exp, val])
