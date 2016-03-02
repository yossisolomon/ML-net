#!/usr/bin/python
import argparse
import logging
import random
import os
from netaddr import iter_iprange

baseCommand = "ITGSend -m rttm -a"

# IPs
firstHost = "10.0.0.1"
lastHostTemplate = "10.0.0."

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
dynamicPPS = {}
dynamicPPS["min"] = 615 # ~60% of 10 Mbit
dynamicPPS["max"] = 920 # ~90% of 10Mbit

defaultPacketSize = 1024


def create_command(base, dest, duration, delay, pps, size):
    cmd = base
    cmd += " %s"%dest
    cmd += " -t %s"%duration
    cmd += " -d %s"%delay
    cmd += " -O %s"%pps
    cmd += " -c %s"%size
    cmd += " < /dev/null &"
    return cmd


def create_dynamic_loader_commands(hosts):
    commands = []
    for i in xrange(periods):
        delay = i * periodLengthMilliSeconds + random.randrange(delayRandomness["min"],delayRandomness["max"])
        pps = random.randrange(dynamicPPS["min"],dynamicPPS["max"])
        loaded_host = hosts[random.randrange(len(hosts))]
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
        f.write("#!/bin/bash"+os.linesep)
        map(lambda c: f.write(c+os.linesep),cmds)
        f.write("wait"+os.linesep)
    # give it executable permissions
    st = os.stat(filename)
    os.chmod(filename, st.st_mode | 0111)



def validate_args(args):
    if os.path.isdir(args.config_dir):
        logging.info("Creating config files in: " + args.config_dir)
    else:
        logging.fatal("Argument specified \"" + args.config_dir + "\" is not a directory!")
        exit(1)
    if not 1 <= args.num_hosts <= 253:
        logging.fatal("The number of hosts specified \"" + args.num_hosts + \
              "\" cannot be within one subnet!\nShould be {1..253}!")
        exit(1)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--config-dir",required=True,
                        help="The configuration file directory (where the config files will be written to)")
    parser.add_argument("-n", "--num-hosts", type=int, required=True,
                        help="The number of hosts to generate configuration files for")
    parser.add_argument("--debug", action="store_true", help="Set verbosity to high (debug level)")
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    validate_args(args)


    last_host = lastHostTemplate + str(args.num_hosts)
    ip_addresses = list(iter_iprange(firstHost, last_host, step=1))

    logging.info("Creating configuration for IPs:")
    logging.info(ip_addresses)

    for l in ip_addresses:
        cmds = create_dynamic_loader_commands(ip_addresses)
        logging.info("Creating commands for " + str(l))
        logging.debug(cmds)
        write_cmds_to_file(cmds, args.config_dir+"/config-%s"%(l))

    logging.info("Done generating host config files!")
