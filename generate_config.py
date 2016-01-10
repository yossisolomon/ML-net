#!/usr/bin/python
import random
import os
from netaddr import iter_iprange
baseCommand = "-m rttm -a"
loadedHost = "10.0.0.4"
firstHost = "10.0.0.1"
lastHost = '10.0.0.9'
expDurationMinutes = 200
expDurationSeconds = expDurationMinutes*60
expDurationMilliSeconds = 1000*expDurationSeconds

periodLengthMilliSeconds = 240*1000
periodSendLength = 220 * 1000

#Not designed for more than two yet!
loaderHosts = 2

defaultPacketSize = 1024


def create_command(base, dest, duration, delay, pps, size):
    cmd = base
    cmd += " %s"%dest
    cmd += " -t %s"%duration
    cmd += " -d %s"%delay
    cmd += " -C %s"%pps
    cmd += " -c %s"%size
    return cmd


def create_loader_hosts_commands(numHosts, periodDuration, totalDuration):
    periods = totalDuration/periodDuration
    commands = [[] for _ in xrange(numHosts)]
    for i in xrange(periods):
        for h in xrange(numHosts):
            delay = i * periodLengthMilliSeconds + random.randrange(0,20000)
            pps = random.randrange(384,512)
            commands[h].append(create_command(baseCommand,loadedHost,periodSendLength,delay,pps,defaultPacketSize))
    return commands



steadyStateHostCommand = create_command(baseCommand,loadedHost, expDurationMilliSeconds, 0, 128, defaultPacketSize)
loaderHostsCommands = create_loader_hosts_commands(loaderHosts,periodLengthMilliSeconds,expDurationMilliSeconds)
print "steady loader:"
print steadyStateHostCommand
with open("./config-10.0.0.3","w") as f:
    f.write(steadyStateHostCommand+os.linesep)
print "dynamic loaders:"
print loaderHostsCommands
for h in xrange(loaderHosts):
    with open("./config-10.0.0.%s"%(h+1),"w") as f:
        map(lambda c: f.write(c+os.linesep),loaderHostsCommands[h])

print "background loaders:"
backgroundLoaders = iter_iprange(loadedHost, lastHost, step=1)
for l in backgroundLoaders:
    with open("./config-%s"%(l),"w") as f:
        if str(l) == lastHost:
            cmd = create_command(baseCommand, firstHost, expDurationMilliSeconds, 0, 128, defaultPacketSize)
        else:
            cmd = create_command(baseCommand,l+1, expDurationMilliSeconds, 0, 128, defaultPacketSize)
        print cmd
        f.write(cmd+os.linesep)