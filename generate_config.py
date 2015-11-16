#!/usr/bin/python
import random
import os
baseCommand = "-m rttm -a 10.0.0.4"

expDurationMinutes = 25
expDurationSeconds = expDurationMinutes*60
expDurationMilliSeconds = 1000*expDurationSeconds

periodLengthMilliSeconds = 30*1000
periodSendLength = 10 * 1000

#Not designed for more than two yet!
loaderHosts = 2

defaultPacketSize = 1024

def create_command(base, duration, delay, pps, size):
    cmd = base
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
            delay = i * periodLengthMilliSeconds + random.randrange(1000,10000)
            pps = random.randrange(128,576)
            commands[h].append(create_command(baseCommand,periodSendLength,delay,pps,defaultPacketSize))
    return commands



steadyStateHostCommand = create_command(baseCommand, expDurationMilliSeconds, 0, 128, defaultPacketSize)
loaderHostsCommands = create_loader_hosts_commands(loaderHosts,periodLengthMilliSeconds,expDurationMilliSeconds)
print "steady:"
print steadyStateHostCommand
with open("./config-10.0.0.3","w") as f:
    f.write(steadyStateHostCommand+os.linesep)
print "loaders:"
print loaderHostsCommands
for h in xrange(loaderHosts):
    with open("./config-10.0.0.%s"%(h+1),"w") as f:
        map(lambda c: f.write(c+os.linesep),loaderHostsCommands[h])
