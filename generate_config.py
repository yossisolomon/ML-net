#!/usr/bin/python
import random
import os
from netaddr import iter_iprange


baseCommand = "-m rttm -a"

# IPs
loadedHost = "10.0.0.4"
firstHost = "10.0.0.1"
steadyLoader = "10.0.0.3"
lastHost = '10.0.0.9'

expDurationMinutes = 200
expDurationSeconds = expDurationMinutes*60
expDurationMilliSeconds = 1000*expDurationSeconds

periodLengthMilliSeconds = 240*1000
periodSendLength = 220 * 1000
periods = expDurationMilliSeconds/periodLengthMilliSeconds

delayRandomness = {}
delayRandomness["min"] = 0
delayRandomness["max"] = 20000

# Packets per Second
steadyPPS = 128
dynamicPPS = {}
dynamicPPS["min"] = 384
dynamicPPS["max"] = 512

defaultPacketSize = 1024

# Not designed for more than two yet!
dynamicLoaderHostsNum = 2


def create_command(base, dest, duration, delay, pps, size):
    cmd = base
    cmd += " %s"%dest
    cmd += " -t %s"%duration
    cmd += " -d %s"%delay
    cmd += " -C %s"%pps
    cmd += " -c %s"%size
    return cmd


def create_dynamic_loader_commands(loaded_host):
    commands = []
    for i in xrange(periods):
        delay = i * periodLengthMilliSeconds + random.randrange(delayRandomness["min"],delayRandomness["max"])
        pps = random.randrange(dynamicPPS["min"],dynamicPPS["max"])
        cmd = create_command(baseCommand, loaded_host, periodSendLength, delay ,pps, defaultPacketSize)
        commands.append(cmd)
    return commands


def create_dynamic_loaders_commands(loaded_host, num_hosts):
    commands = [[] for _ in xrange(num_hosts)]
    for h in xrange(num_hosts):
        commands[h].extend(create_dynamic_loader_commands(loaded_host))
    return commands


def write_cmds_to_file(cmds, filename):
    with open(filename,"w") as f:
        map(lambda c: f.write(c+os.linesep),cmds)


print "steady loader:"
steadyStateHostCommand = create_command(baseCommand, loadedHost, expDurationMilliSeconds, 0, steadyPPS, defaultPacketSize)
print steadyStateHostCommand
write_cmds_to_file([steadyStateHostCommand], "./config-"+steadyLoader)

print "dynamic loaders:"
loaderHostsCommands = create_dynamic_loaders_commands(loadedHost, dynamicLoaderHostsNum)
print loaderHostsCommands
for h in xrange(dynamicLoaderHostsNum):
    write_cmds_to_file(loaderHostsCommands[h],"./config-10.0.0.%s"%(h+1))


print "background loaders:"
backgroundLoaders = iter_iprange(loadedHost, lastHost, step=1)
for l in backgroundLoaders:
    if str(l) == lastHost:
        cmds = create_dynamic_loader_commands(firstHost)
    else:
        cmds = create_dynamic_loader_commands(l+1)
    print str(l) + ":"
    print cmds
    write_cmds_to_file(cmds, "./config-%s"%(l))
