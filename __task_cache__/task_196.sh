#!/bin/bash
source vasp/6.3.2/oneapi_latest
MPIRUN=mpirun #Intel mpi and Open MPI
source alias.sh
shopt -s  expand_aliases
shopt expand_aliases
for i in *;do
    if [ ! -d $i ];then
        continue;
    fi
    cd $i;
    incar;
    kpotcar;
    pre vdw EDIFF_1E-05 EDIFFG_-0.03 NCORE_16 ispin;

    echo "Starting Time is `date`" >>display
    echo "Directory is `pwd`" >>display
    $MPIRUN vasp_std >>display
    echo "Ending Time is `date`" >>display

    #calculate single point energy
    mkdir single_point;
    cp CONTCAR single_point/POSCAR;
    cp KPOINTS POTCAR INCAR single_point;
    cd single_point;
    pre kd scf;

    echo "Starting Time is `date`" >>display
    echo "Directory is `pwd`" >>display
    $MPIRUN vasp_std >>display
    echo "Ending Time is `date`" >>display

    cd ../../;
done

