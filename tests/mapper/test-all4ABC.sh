#!/bin/sh
ARGS="doC eager generate=failed,one $@"
for a in None A0 A1 B0 B1 C0 C1; do
   	echo ... $a
   	PYTHONPATH=$PYTHONPATH:.. python test_ABC_inh_ref_all.py Clinks=$a $ARGS >all_$a 2>&1
	mv -f _test_ABC_all.py _t_$a.py
done

