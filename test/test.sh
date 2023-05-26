#!/bin/bash
for i in {1..10};do
	sleep 1
	echo $i >> test.txt
done
