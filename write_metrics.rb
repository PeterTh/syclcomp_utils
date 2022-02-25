require 'fileutils'

IMPLEMENTATION_VERSIONS = {
        "ccpp" => ["2_4", "2_5", "2_6", "2_7", "2_8"],
        "dpcpp_s" => ["2022-01-13", "2021-11-14", "2021-09-15"],#, "2021-05-18"
        "dpcpp_n" => ["2022-01-13", "2021-11-14", "2021-09-15"],#, "2021-05-18"
        "dpcpp_ns" => ["2022-01-13", "2021-11-14", "2021-09-15"],#, "2021-05-18"
        "hipSYCL" => ["2021-03-19","2021-05-18","2021-07-17","2021-09-15","2022-01-13"], #"2021-11-14",
        "triSYCL" => [""]
}

def get_metrics(array, position)
    IMPLEMENTATION_VERSIONS.each do |impl, versions|
        versions.each do |version|
            Dir.chdir("#{impl}/#{version}") do

                Dir.each_child(Dir.pwd) {
                    |exp_name| unless exp_name.include? "." then 
                        Dir.chdir(exp_name) do
                            #p Dir.pwd

                            Dir.each_child(".") { |val|
                                Dir.chdir("#{val}") do
                                    #p Dir.pwd

                                    Dir.each_child(".") { |rep|
                                        Dir.chdir(rep) do 
                                            p Dir.pwd
                                            file = File.open("#{EXP_RESULT}").read

                                            file.gsub!(/(\r|\n)+/,"\n")
                                            measures = file.split(/\n/)
                                            #array.append(measures[position].to_f)
                                            array["#{impl}"]["#{version}"]["#{exp_name}"]["#{val}"]["#{rep}"] = measures[position].to_f
                                        end
                                    }
                                end
                            }
                        end
                    end
                }
            end
        end
    end
end

accumulated_error = 0.0
count = 0
first = 0
second = 0

EXP_RESULT = "exp.results"

if ARGV.length != 1
    puts "Wrong args"
    exit
else
    path_first = ARGV[0]
end

p "pf #{path_first}"

first = Hash.new {  |h, k| h[k] = h.dup.clear}
Dir.chdir("#{path_first}") do
    get_metrics(first,-1)
end
puts "done with f"


p first[-1]

File.write("metrics", first)
