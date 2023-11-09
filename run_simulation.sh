#!/bin/csh -f

cd $PWD

rm -rf ./symlinks/.*.addr
rm -rf ./symlinks/.*.port
sleep 1
xterm -T "BRIDGE cs1" -iconic -e python3 bridge.py cs1 8 &
xterm -T "BRIDGE cs2" -iconic -e python3 bridge.py cs2 8 &
xterm -T "BRIDGE cs3" -iconic -e python3 bridge.py cs3 8 &
sleep 1
xterm -T "Host A" -e python3 station.py -no ifaces/ifaces.a rtables/rtable.a hosts &
sleep 1
xterm -T "Host B" -e python3 station.py -no ifaces/ifaces.b rtables/rtable.b hosts &
sleep 1
xterm -T "Host C" -e python3 station.py -no ifaces/ifaces.c rtables/rtable.c hosts &
sleep 1
xterm -T "Host D" -e python3 station.py -no ifaces/ifaces.d rtables/rtable.d hosts &
sleep 1
xterm -T "Host E" -e python3 station.py -no ifaces/ifaces.e rtables/rtable.e hosts &
sleep 1
xterm -T "Router r1" -iconic -e python3 station.py -route ifaces/ifaces.r1 rtables/rtable.r1 hosts &
xterm -T "Router r2" -iconic -e python3 station.py -route ifaces/ifaces.r2 rtables/rtable.r2 hosts &
