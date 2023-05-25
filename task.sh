#!/bin/bash
echo $SLURM_JOB_NODELIST >> test.txt
for i in {1..10};do
	sleep 1
	echo 1 >> test.txt
    done
