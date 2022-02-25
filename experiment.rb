# compile time benchmarking experiment script

# uses compiletime_gen to generate various programs and measures their compile time

# NOTES:
# - needs a "time" command line tool which produces standard GNU time format output (otherwise, adapt build_and_get_result)
# - REPEATS defines the number of measurements per data point
# - MAX_POW defines the maximum for the kernel_num, buffer_num and capture_num runs (max = 2^MAX_POW)
# - BASELINE_K defines the base number of kernels used for other runs
# - MIX_NUM defines the basic number of instructions per class for the -mix parameter test

require 'parallel'
require 'fileutils'

NUM_PARALLEL_RUNS = 32

REPEATS = 50
MAX_POW = 10

BASELINE_K = 100
MIX_NUM = 25

COMP_BENCH = "/software-local/comp-bench"
CCPP_PATH = COMP_BENCH + "/ccpp"
DPCPP_PATH = COMP_BENCH + "/dpcpp"
HIP_PATH = COMP_BENCH + "/hipSYCL/build"
TRI_PATH = COMP_BENCH + "/triSYCL"

## Check directory requirements ------------------------------------

if File.exists?("compiletime.cpp")
        puts "You probably don't want to run experiment.rb in the source path."
        puts 'Create a path for your experiment and run "ruby path/to/sycl-bench/compiletime/experiment.rb" from there.'
        exit -1
end

RESULT_FN = "exp.results"
ERROR_FN = "exp.error.log"
OUTPUT_FN = "output"

## Helper function ------------------------------------

def build_and_get_result(target_config_params, impl, version)

        flags = "#{target_config_params} -I#{Dir.pwd} -o #{OUTPUT_FN} "
        if impl.include? "ccpp" then
                compiler_path="#{CCPP_PATH}/#{version}/bin/compute++"
        elsif impl.eql?"dpcpp_s" then
                compiler_path="#{DPCPP_PATH}/#{version}/bin/clang++" 
                flags += "-I#{DPCPP_PATH}/#{version}/include/sycl -fsycl -Wl,-rpath=/software-local/comp-bench/dpcpp/#{version}/lib  -fsycl-targets=spir64"
                flags += "-I#{CCPP_PATH}/#{version}/include -sycl -I/usr/local/cuda/include -Rsycl-serial-memop -Rsycl-kernel-naming"
        elsif impl.eql?"dpcpp_n" then
                compiler_path="#{DPCPP_PATH}/#{version}/bin/clang++" 
                flags += "-I#{DPCPP_PATH}/#{version}/include/sycl -fsycl -Wl,-rpath=/software-local/comp-bench/dpcpp/#{version}/lib  -fsycl-targets=nvptx64-nvidia-cuda"
        elsif impl.eql?"dpcpp_ns" then
                compiler_path="#{DPCPP_PATH}/#{version}/bin/clang++" 
                flags += "-I#{DPCPP_PATH}/#{version}/include/sycl -fsycl -Wl,-rpath=/software-local/comp-bench/dpcpp/#{version}/lib  -fsycl-targets=spir64,nvptx64-nvidia-cuda"
        elsif impl.include? "hip" then
                compiler_path="#{HIP_PATH}/#{version}/install/bin/syclcc"
                flags += "--hipsycl-gpu-arch=sm_75"
        else
                # triSYCL
                compiler_path="clang++-10"
                flags += "-I#{TRI_PATH}/include -I#{TRI_PATH}/build/_deps/experimental_mdspan-src/include -std=c++20 -fopenmp"
        end
        res = `time #{compiler_path} #{__dir__}/codegen/compiletime.cpp #{flags}  2>&1`

        # delete output files
        FileUtils.rm_f(Dir.glob("#{OUTPUT_FN}*"))
        
        if res =~ /non-zero status/
                puts "!!!! ERROR #{Dir.pwd}"
                File.write(ERROR_FN, res)
        end
        if res =~ /(\d+\.\d+)user (\d+\.\d+)system/
                return ($1.to_f + $2.to_f)
        else
                puts "!!!! Couldn't parse!"
                puts "-----------"
                puts res
                puts "-----------"
                exit -2
        end
end

## Experiments varying single parameter ------------------------------------

TARGET_CONFIGS = {
        "debug" => "-g -O0",
        "release" => "-O2"
}

SINGLE_PARAM_EXPERIMENTS = [
        ["kernel_num", "-k", MAX_POW.times.to_a.map { |n| 2**n }],
        ["buffer_num", "-b", MAX_POW.times.to_a.map { |n| 2**n }],
        ["capture_num", "-c", MAX_POW.times.to_a.map { |n| 2**n }],
        ["dimensions", "-k #{BASELINE_K} -d", [1,2,3]],
        ["loopnests", "-k #{BASELINE_K} -l", [1,2,3,4,5,6]],
        ["type", "-k #{BASELINE_K} -t", %i[int float double]],
        ["mix", "-k #{BASELINE_K/2} -m", ["add:#{MIX_NUM*4}", "mad:#{MIX_NUM*4}", "cos:#{MIX_NUM*4}", "sqrt:#{MIX_NUM*4}", "mad:#{MIX_NUM*2},cos:#{MIX_NUM*2}", "add:#{MIX_NUM},mad:#{MIX_NUM},cos:#{MIX_NUM},sqrt:#{MIX_NUM}"]],
]

ENV['C_INCLUDE_PATH'] = "#{Dir.pwd}:"
ENV['CPLUS_INCLUDE_PATH'] = "#{Dir.pwd}:"

IMPLEMENTATION_VERSIONS = {
        "ccpp" => ["2_4", "2_5", "2_6", "2_7", "2_8"],
        "dpcpp_s" => ["2022-01-13", "2021-11-14", "2021-09-15"]
        "dpcpp_n" => ["2022-01-13", "2021-11-14", "2021-09-15"]
        "dpcpp_ns" => ["2022-01-13", "2021-11-14", "2021-09-15"]
        "hipSYCL" => ["2021-03-19","2021-05-18","2021-07-17","2021-09-15","2022-01-13"]
        "triSYCL" => [""]
}

experiments = []
REPEATS.times do |rep|
        TARGET_CONFIGS.each do |target_config_name, target_config_params|
                IMPLEMENTATION_VERSIONS.each do |impl, versions|
                        versions.each do |version|
                                SINGLE_PARAM_EXPERIMENTS.each do |exp_name, exp_arg, exp_values|
                                        exp_values.each do |val|
                                                experiments <<= [rep, target_config_name, target_config_params, impl, version, exp_name, exp_arg, val]
                                        end
                                end
                        end
                end
        end
end

puts experiments.size

Parallel.each(experiments, in_processes: NUM_PARALLEL_RUNS, progress: "Running experiments") do |experiment|
        rep, target_config_name, target_config_params, impl, version, exp_name, exp_arg, val = experiment
        exp_dir = "#{target_config_name}/#{impl}/#{version}/#{exp_name}/#{val}/#{rep}"
        FileUtils.mkdir_p(exp_dir)
        puts exp_dir
        Dir.chdir(exp_dir) do
                `ruby #{__dir__}/codegen/compiletime_gen.rb #{exp_arg} #{val}`
                result = build_and_get_result(target_config_params, impl, version)
                File.write("#{RESULT_FN}", "#{result.inspect}\n", mode:"a")
        end
end

