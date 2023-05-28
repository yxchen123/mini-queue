#!/bin/bash
MPIRUN=mpirun #Intel mpi and Open MPI
source alias.sh
shopt -s  expand_aliases
shopt expand_aliases
    incar;
    kpotcar;
    DFT+U_from_poscar.py;
    pre vdw EDIFF_1E-05 EDIFFG_-0.03 NCORE_16;
    /opt/bin/optkit/opt_vasp vasp_std >> display;
    mv INCAR_best INCAR
    echo "Starting Time is `date`" >>display
    echo "Directory is `pwd`" >>display
    $MPIRUN vasp_std >>display
    echo "Ending Time is `date`" >>display
