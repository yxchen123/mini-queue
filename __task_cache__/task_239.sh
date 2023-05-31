#!/bin/sh
#An example for MPI job.
#SBATCH -J job_name
#SBATCH -o job-%j.log
#SBATCH -e job-%j.err
#SBATCH -p CPU-64C256GB
#SBATCH -N 3 -n 192
NODELIST=$SLURM_JOB_NODELIST
while true;do
run_tasks.py $NODELIST
done
