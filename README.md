SYCLCOMP Utilities
==================

This repository contains a code generator and a set of scripts to investigate the compilation speed of various SYCL platforms.

Prerequisites
-------------

The programs and scripts in this repository require the Ruby and Python scripting languages as well as various library dependencies in each of them which will be reported as missing if they are not available. 

Additionally, compiling and installing each SYCL implementation requires all of its associated dependencies, as outlined in the respective documentation.

Overview
--------

The following are included in this repository:
 
 * `codegen`: the code generation infrastructure. Provides documentation of command line parameters with `-h` and can be further configured in the script.
 * `*_build_revisions.rb`: helper scripts to build revisions of the repsective platforms over time.
 * `experiments.rb` and `write_metrics.rb`: scripts for running experiments and gathering metrics from them.
 * `plot_*.py`: scripts for generating plots from the gathered metrics.

Usage
-----

What follows is a short guide to the scrips used in the experiments. The experiments can be reproduced in 4 major steps:

1. **Platform Preparation**

   First, the most recent github revision of triSYCL, dpcpp and hipSYCL need to be checked out from their respective github repositories into paths of the same name. For triSYCL, as it is used in a header-only fashion, and only the most recent revision is tested, preparation is now complete.

   For dpcpp and hipSYCL, the two scripts `{version}_build_revisions.rb` need to be configured, setting the `COMP_BENCH` path. Then, run `ruby {version}_build_revisions.rb` to build the folders containing each revision over time. These script should create the folder structure, and then download and build the respective versions. This will take a significant amount of time.
   
   As for ComputeCPP, one needs to obtain and install the corresponding binaries from the [official website](https://developer.codeplay.com/products/computecpp/ce/home).

2. **Experiment Runs**

    All platform paths, the experiments to run, as well as the number of iterations can be configured in `experiments.rb`.
    Running this script with `ruby experiment.rb` (ideally from a ramdisk location if using parallel experiments) will generate the following folder structure:


        ├── release
            ├── ccpp
            │   └── versions
            ├── dpcpp_s
            │   └── versions
            ├── dpcpp_n
            │   └── versions
            ├── dpcpp_ns
            │   └── versions
            ├── hipsycl
            │   └── versions
            └── trisycl
                └── version
        └── debug
                ├── ccpp
                │   └── versions
                ├── dpcpp_s
                │   └── versions
                ├── dpcpp_n
                │   └── versions
                ├── dpcpp_ns
                │   └── versions
                ├── hipsycl
                │   └── versions
                └── trisycl
                    └── version

3. **Gathering of Metrics**

    Run `ruby write_metrics /path/to/release` and to generate a `metrics` file used for plotting. The same can be done but with `path/to/debug` instead.

4. **Plotting** 
    
    Several scripts are included which plot different charts. These all run with python3 and they require matplotlib, numpy, collections, json, sys, statistics and datetime. Each script requires its own set of arguments, but running the "plot_all" variants will call the corresponding scripts with all the possible arguments, mixing implementations, versions and experiments, when possible.
