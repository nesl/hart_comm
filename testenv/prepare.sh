#!/bin/bash

# remove files / kill processes
kill -9 `ps aux | grep student_bin | awk '{print $2}'`
cd "$(dirname "$0")"
rm files/*

# mount module
if [ ! -c /dev/ptp1 ]; then
    capes BBB-AM335X
    echo 'no'
fi

config-pin overlay cape-universala
config-pin P8_8 timer
config-pin P8_10 timer
