#!/bin/bash
source vasp/6.3.2/oneapi_latest
MPIRUN=mpirun #Intel mpi and Open MPI
source alias.sh
shopt -s  expand_aliases
shopt expand_aliases

cp POSCAR init_POSCAR
cp CONTCAR POSCAR;
incar;
pre ispin vdw EDIFF_1E-05 EDIFFG_-0.03 NCORE_16;
kpotcar;

#执行VASP
echo "Starting Time is `date`" >>display
echo "Directory is `pwd`" >>display
/opt/bin/optkit/opt_vasp vasp_std;
mv INCAR_best INCAR
$MPIRUN vasp_std >>display
echo "Ending Time is `date`" >>display

#判断当前路径是否包含slab里
if [[ `pwd` != *"slab"* ]]; then
    mkdir zpe;
    cp CONTCAR zpe/POSCAR;
    cp KPOINTS POTCAR INCAR zpe;
    cd zpe;
    pre zpe;
    fix_ads_atoms.py;
    cp POSCAR bak_POSCAR;
    mv POSCAR_FIX POSCAR;
    echo "Starting Time is `date`" >>display
    echo "Directory is `pwd`" >>display
    $MPIRUN vasp_std >>display
    echo "Ending Time is `date`" >>display
    cd ../;
fi

