# source this file, don't run it, then you get jobs
./run_of_three.sh 5000 >& s0.out & ./run_of_three.sh 5001 >& s1.out & ./run_of_three.sh 5002 >& s2.out &

