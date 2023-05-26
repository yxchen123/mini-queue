# mini-queue
Supercomputer center subqueue system, to achieve the function of exclusive computing resources on demand

## Installation Guide

```shell
cd /Any_path_you_like;
git clone https://github.com/yxchen123/mini-queue.git
cd mini-queue;
./setup.sh;
source ~/.bashrc;
```





## Instructions

### Step 1:make a Worker_submit.sh

```shell
#!/bin/bash
#An example for MPI job. Note:It may vary from supercomputer center to supercomputer center
#SBATCH -J job_name
#SBATCH -o job-%j.log
#SBATCH -e job-%j.err
#SBATCH -p CPU-64C256GB
#SBATCH -N 2 -n 128

NODELIST=$SLURM_JOB_NODELIST

while true;do
	run_tasks.py $NODELIST
done
```

This worker will constantly detect if a task exists in the mini-queue, and if it does, it runs, otherwise it waits.



Of course, you can submit as many workers as you want to grab tasks from the mini-queue at the same time



## Step 2: Manage, view, and submit tasks

```shell
#Once the Worker has applied for computing resources in the cluster, the queue is up to you.
#such as slurm system.
>> sbatch Worer_submit.sh
Submitted batch job 19672

>> squeue -u user_name
             JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
             19672 CPU-64C25 job_name   yxchen  R       0:07      2 cnode[66-67]

#your worker is warmed up and ready to go
>> cd Workdir (optional)
>> ssbatch task.sh
Submit mini-queue batch job 6
>> qqa
TASKID         NAME           ST             TIME           NodeList       
6              mpi_job.sh     R             0-00:00:05     cnode[66-67]
>> ssbatch task.sh
Submit mini-queue batch job 7

>> qqa
TASKID         NAME           ST             TIME           NodeList       
6              mpi_job.sh     R             0-00:00:10     cnode[66-67] 
7              mpi_job.sh     PD            0-00:00:00     (Priority)  

>> qqw
TASKID         ST             WorkDir        
6              R             /gpfs/home/scms/yxchen/cyx/mini-test
7              PD             /gpfs/home/scms/yxchen/cyx/mini-test

#if you want to cancel a job, you can sscancel + TASKID
>> sscancel 6

>> qqa
TASKID         NAME           ST             TIME           NodeList       
6              mpi_job.sh     C              0-00:00:00     (Priority)     
7              mpi_job.sh     R              0-00:00:01     (Priority)

#wait a moment
>> qqa
TASKID         NAME           ST             TIME           NodeList        
7              mpi_job.sh     R              0-00:00:05     (Priority)
```
