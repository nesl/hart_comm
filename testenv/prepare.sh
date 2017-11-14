#!/bin/bash

# remove files / kill processes
kill -9 `ps aux | grep student_bin | awk '{print $2}'`
cd "$(dirname "$0")"
rm files/*

# load module
if [ ! -c /dev/ptp1 ]; then
    capes BBB-AM335X
    echo 'no'
fi

# config-pin
config-pin overlay cape-universala
config-pin P8_8 timer
config-pin P8_10 timer

# flush the queue timestamps
testptp -d /dev/ptp1 -i 1 -L 1,1 >/dev/null 2>&1
testptp -d /dev/ptp1 -i 1 -e 100 >/dev/null 2>&1 &

PID=$!
echo PTP flushing process launched at PID $PID.

sleep 1

kill -TERM $PID

echo "PTP queue flushed."
