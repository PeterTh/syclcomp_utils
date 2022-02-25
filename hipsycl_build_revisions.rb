require 'benchmark'
require 'date'

NUM_STEPS = 6
STEP_SIZE = 60 # days

COMP_BENCH = "/software-local/comp-bench"
REPO_PATH = COMP_BENCH + "/hipSYCL"

def run_git_checkout(before_date)
    Dir.chdir(REPO_PATH) do
        `git checkout \`git rev-list -1 --before="#{before_date.iso8601}" develop --\` > ../#{before_date.iso8601}_checkout.log 2>&1`
    end
end

def configure_and_build(before_date)
    Dir.chdir(REPO_PATH) do
        diso = before_date.iso8601
        p diso
        `mkdir #{diso}`
        Dir.chdir(diso) do
            `cmake .. -G Ninja -DCMAKE_INSTALL_PREFIX="/software-local/comp-bench/hipSYCL/#{diso}/install" -DWITH_CUDA_BACKEND=1 -DCMAKE_BUILD_TYPE=Release -DHIPSYCL_PLATFORM=cuda -DHIPSYCL_GPU_ARCH=sm_75`
            `ninja > ../#{diso}_build.log 2>&1`
            `ninja install > ../#{diso}_install.log 2>&1`
        end
    end
end

def compile_simple(before_date, dir)
    Dir.chdir(dir)
    #p `ls`
    diso = before_date.iso8601
    time = Benchmark.realtime {
        `#{REPO_PATH}/#{diso}/install/bin/syclcc simple_sycl.cpp  -O2 --hipsycl-gpu-arch=sm_75 -o #{diso}`
    }
    File.write("compilation_time_hipsycl.txt", "#{diso} - #{time}\n", mode:"a")
end

start_date = Date.new(2022,1,13)
dir = Dir.pwd
NUM_STEPS.times do
    #puts "checkout"
    run_git_checkout(start_date)
    #puts "configure"
    configure_and_build(start_date)
    #puts "compile"
    compile_simple(start_date, dir)
    start_date -= STEP_SIZE
end

