#!/usr/bin/python
import argparse
import os
import time
import logging
from os.path import join as pj

startDatagram ='startDatagram =================================\n'
endDatagram ='endDatagram   =================================\n'
startSample = 'startSample ----------------------\n'
endSample = 'endSample   ----------------------\n'
disregardCounter = ['sampleType_tag','sourceId', 'counterBlock_tag', 'networkType', 'ifSpeed', 'ifDirection', 'ifStatus', 'ifInBroadcastPkts','ifInUnknownProtos','ifOutMulticastPkts','ifOutBroadcastPkts','ifPromiscuousMode']
relevantKeys = ['ifOutOctets','ifOutUcastPkts','ifInOctets','ifInUcastPkts']
timeKey = 'time'
mega = pow(2,20)
megaByte = mega/8


def get_interfaces_to_names_map(baseFolder):
    interfaces = {}
    with open(pj(baseFolder,'intfs-list')) as inputFile:
        line = inputFile.readline()
        while not line == '':
            k,v = get_key_value_from_line(line,': ')
            interfaces[k] =v
            line = inputFile.readline()
    return interfaces


def get_datagrams(baseFolder):
    datagrams = []
    with open(pj(baseFolder,'sflow-datagrams')) as inputFile:
        line = inputFile.readline()
        while not line == '':
            if line == startDatagram:
                datagrams.append(get_datagram_map(inputFile))
            line = inputFile.readline()
    return datagrams


def get_datagram_map(inputFile):
    l = inputFile.readline()
    datagram = {}
    datagram['samples'] = []
    while not l == endDatagram:
        if l == startSample:
            datagram['samples'].append(get_sample_map(inputFile))
        else:
            k,v = get_key_value_from_line(l)
            datagram[k] = v
        l = inputFile.readline()
    return datagram


def get_sample_map(inputFile):
    l = inputFile.readline()
    sample = {}
    while not l == endSample:
        k,v = get_key_value_from_line(l)
        if not k in disregardCounter:
            sample[k] = v
        l = inputFile.readline()
    return sample


def get_key_value_from_line(line, delim=' '):
    split = line.replace('\n','').split(delim)
    return split[0] , split[1]


def get_relevant_sampling(sample, timestamp):
    new_sample = {timeKey:timestamp}
    for k in relevantKeys:
        new_sample[k] = sample[k]
    return new_sample




def get_port_to_samples_map(datagrams, interfaces_to_names):
    port_to_samples = {}
    max_time = 0
    min_time = 1000000000000000000
    for d in datagrams:
        time = d['unixSecondsUTC']
        max_time = max(max_time,time)
        min_time = min(min_time,time)
        for s in d['samples']:
            # only accept counter samples which exist in the name mapping
            if s['sampleType'] == 'COUNTERSSAMPLE' and interfaces_to_names.has_key(s['ifIndex']):
                name = interfaces_to_names[s['ifIndex']]
                if not port_to_samples.has_key(name):
                    port_to_samples[name] = [get_relevant_sampling(s,time)]
                else:
                    port_to_samples[name].append(get_relevant_sampling(s,time))
    return port_to_samples, min_time, max_time



def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-dir", default="/tmp",
                        help="The directory where the interfaces and datagram log files can be found")
    parser.add_argument("-o", "--output-dir", default="/tmp",
                        help="The directory into which switch csv files will be written")
    parser.add_argument("-t","--threshold",default=0.76,type=float,help="Overload threshold percentage [0,1]")
    parser.add_argument("-b","--bandwidth",default=100,type=int,help="Link bandwidth [MB/s]")
    parser.add_argument("-s","--segments",default=10,type=int,help="Number of Segments to split samples to")
    parser.add_argument("-d","--debug", action="store_true", help="Set verbosity to high (debug level)")
    args = parser.parse_args()
    args.overload_byte_rate = args.bandwidth * megaByte * args.threshold
    return args


def create_sampling_csv(index_to_samples,sorted_if_names,destIfName,overloadByteRate):
    csv = ''
    for i in sorted(index_to_samples.keys(),key=int):
        values = []
        for eth in sorted_if_names:
            values.append(eth)
            values.append(index_to_samples[i][eth][timeKey])
            for k in relevantKeys:
                values.append(index_to_samples[i][eth][k])
                delta = get_delta(eth, i, index_to_samples, k)
                values.append(delta)
        csv += ', '.join(values) + os.linesep
    return csv


def write_interface_csvs_to_files(filtered_index_to_samples, sorted_if_names, overload_byte_rate, output_folder):
    for interf in sorted_if_names:
        csv = create_sampling_csv(filtered_index_to_samples, sorted_if_names, interf, overload_byte_rate)
        csv_filename = pj(output_folder, "sflow-" + interf + ".csv")
        logging.info("Writing csv for " + interf + " to " + csv_filename)
        logging.debug(csv)
        with open(csv_filename,'w') as f:
            f.write(csv)


def main():
    args = parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    logging.info("Overload Threshold: " + \
                 str(args.overload_byte_rate) + " B/s" + " which is " + str(args.threshold) + "% of link")

    interfaces_to_names = get_interfaces_to_names_map(args.input_dir)
    relevant_interfaces = dict(filter(lambda (i,n): "-eth" in n and not "root" in n,interfaces_to_names.items()))
    
    datagrams = get_datagrams(args.input_dir)
    port_to_samples, min_time, max_time = get_port_to_samples_map(datagrams, relevant_interfaces)

    experiment_len = max_time - min_time
    segment_len = experiment_len / args.segments
    
    for i in xrange(min_time, min_time + segment_len * args.segments):
        # split to the different intervals
           
	
    
if __name__ == '__main__':
    main()

