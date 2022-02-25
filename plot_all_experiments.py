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

EXPERIMENTS = ["kernel_num", "buffer_num",
               "capture_num", "dimensions", "loopnests", "type", "mix"]


# desired_implementation = sys.argv[1]
# if desired_implementation not in IMPLEMENTATION_VERSIONS.keys():
#     print(
#         f"First argument must be one of {[i for i in IMPLEMENTATION_VERSIONS.keys()]}")
#     exit()

METRICS = "../../release50"
SCRIPT = "../../plot_impl_exp.py"

# python3 ./plot_impl_exp.py ccpp buffer_num release_metrics
for impl in IMPLEMENTATION_VERSIONS.keys():
    for exp in EXPERIMENTS:
        print(
            f"python3 {SCRIPT} {impl} {exp} {METRICS}")
        subprocess.run(
            ["python3", SCRIPT, impl, exp, METRICS])
