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

REL = "../../release50"
SCRIPT = "../../plot_impl_vers.py"
# python3 plot_impl_vers.py release_metrics ccpp
for impl in IMPLEMENTATION_VERSIONS.keys():
    print(
        f"python3 {SCRIPT} {REL} {impl} ")
    subprocess.run(
        ["python3", SCRIPT, REL, impl])
