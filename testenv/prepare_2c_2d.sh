#!/bin/bash

# remove files / kill processes
kill -9 `ps aux | grep student_bin | awk '{print $2}'`
cd "$(dirname "$0")"
rm files/*

# activate pruss
~/Cyclops-PRU/Cyclops_IDE/term-proj/scripts/activate-pruss.sh

# configure pins
config-pin overlay cape-universala
config-pin P8_46 pruout
config-pin -q P8_46
config-pin P8_45 pruin
config-pin -q P8_45
