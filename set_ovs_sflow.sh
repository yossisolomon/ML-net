#!/bin/bash


# a  workaround
_switch=`sudo ovs-vsctl list br | awk -- '/^name/ {print $3; exit;} '`
_switch=`echo $_switch | tr -d "\""`

# analysis setting
collector_ip=127.0.0.1:6343
agent_ip=eth0
header_bytes=128
sampling_n=1000000
polling_sec=1
RUN="sudo ovs-vsctl -- --id=@sflow create sflow \
            agent=${agent_ip}           \
            target=\"${collector_ip}\"  \
            header=${header_bytes}      \
            sampling=${sampling_n}      \
            polling=${polling_sec}      \
            -- set bridge ${_switch} sflow=@sflow"

for br in `sudo ovs-vsctl list br | awk -- '/^name/ {print $3;} '`; do
    br=`echo $br | tr -d "\""`
    RUN="$RUN -- -- set bridge $br sflow=@sflow"
done

echo Running:
echo $RUN
$RUN


