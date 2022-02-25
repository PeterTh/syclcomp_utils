require 'date'

NUM_STEPS = 3
STEP_SIZE = 60 # days

BUILD_PARALLELISM = 32

COMP_BENCH = "/software-local/comp-bench"
REPO_PATH = COMP_BENCH + "/dpcpp"

HIP=false

def get_folder_name(before_date)    
    ret = "#{before_date.iso8601}"
    ret += "_nohip" if !HIP
    ret
end

def run_git_checkout(before_date)
    checkout_fn_prefix = get_folder_name(before_date)
    Dir.chdir(REPO_PATH) do
        `git checkout \`git rev-list -1 --first-parent --before="#{before_date.iso8601}" sycl --\` > ../#{checkout_fn_prefix}_checkout.log 2>&1`
    end
end

def configure_and_build(before_date)
    Dir.chdir(REPO_PATH) do
        diso = get_folder_name(before_date)
        `mkdir #{diso}`
        Dir.chdir(diso) do
            `python3 ../llvm/buildbot/configure.py #{HIP ? "--hip" : ""} --cuda -t release -o . --cmake-gen Ninja > ../#{diso}_configure.log 2>&1`
            `ninja -j #{BUILD_PARALLELISM} > ../#{diso}_build.log 2>&1`
        end
    end
end

start_date = Date.new(2022,1,13)

NUM_STEPS.times do
    folder = get_folder_name(start_date)
    if File.exists?("#{folder}/bin/clang++")
        puts "Skipping #{folder}, already done"
    else
        run_git_checkout(start_date)
        configure_and_build(start_date)
    end
    start_date -= STEP_SIZE
end

