#!/bin/bash
echo Time is `date`
echo Directory is $PWD
echo This job runs on the following nodes:
echo $SLURM_JOB_NODELIST
echo This job has allocated $SLURM_JOB_CPUS_PER_NODE cpu cores.
MPIRUN=mpirun #Intel mpi and Open MPI
echo "Starting Time is `date`" >>display
echo "Directory is `pwd`" >>display
$MPIRUN vasp_std >>display
echo "Ending Time is `date`" >>display

