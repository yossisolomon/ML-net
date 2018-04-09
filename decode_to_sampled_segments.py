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
csv_start = '''
startToncepts
numberOfEntities,'''
disregardCounter = ['sampleType_tag','sourceId', 'counterBlock_tag', 'networkType', 'ifSpeed', 'ifDirection', 'ifStatus', 'ifInBroadcastPkts','ifInUnknownProtos','ifOutMulticastPkts','ifOutBroadcastPkts','ifPromiscuousMode','ifOutUcastPkts','ifInOctets','ifInUcastPkts']
relevantKeys = ['ifOutOctets']
timeKey = 'time'
portKey = 'port'
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


def get_relevant_sampling(sample, name):
    new_sample = {portKey:name}
    for k in relevantKeys:
        new_sample[k] = sample[k]
    return new_sample


def is_active(sample, threshold):
    byte_cnt = int(sample['ifOutOctets'])
    return byte_cnt > threshold
        

def get_time_to_samples_map(datagrams, interfaces_to_names):
    time_to_samples = {}
    max_time = 0
    min_time = 1000000000000000000
    for d in datagrams:
        time = int(d['unixSecondsUTC'])
        max_time = max(max_time,time)
        min_time = min(min_time,time)
        for s in d['samples']:
            # only accept counter samples which exist in the name mapping
            if s['sampleType'] == 'COUNTERSSAMPLE' and interfaces_to_names.has_key(s['ifIndex']):
                port = interfaces_to_names[s['ifIndex']]
                if not time_to_samples.has_key(time):
                    time_to_samples[time] = [get_relevant_sampling(s,port)]
                else:
                    time_to_samples[time].append(get_relevant_sampling(s,port))
    return time_to_samples, min_time, max_time


def create_sampling_csv(segment_len, segments, port_ids, time_to_samples, min_time, overload_byte_rate):
    csv = csv_start + str(segments) + os.linesep
    for segment in xrange(segments):
        collected_intervals = []
        currently_active_intervals = {}
        start = min_time + segment * segment_len
        end = min_time + (segment+1) * segment_len
        for i in xrange(start, end):
            for s in time_to_samples[i]:
                port = s[portKey]
                if is_active(s,overload_byte_rate):
                    if not currently_active_intervals.has_key(port):
                        currently_active_intervals[port] = i
                elif currently_active_intervals.has_key(port):
                        collected_intervals.append({portKey:port, 'start':currently_active_intervals.pop(port) - start + 1 , 'end':i - start + 1})
        for k,v in currently_active_intervals.items():
            collected_intervals.append({portKey:k, 'start': v - start + 1, 'end': end - start + 1})
        csv += str(segment+1) + ',' + str(segment) + ';' + os.linesep
        csv += ';'.join(map(lambda x: str(x['start']) + ',' + str(x['end']) + ',' + port_ids[x[portKey]],collected_intervals)) + os.linesep
   return csv


def write_csv_to_file(csv_filename, csv):
    logging.info("Writing csv to " + csv_filename)
    logging.debug(csv)
    with open(csv_filename,'w') as f:
        f.write(csv)


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
    time_to_samples, min_time, max_time = get_time_to_samples_map(datagrams, relevant_interfaces)

    experiment_len = max_time - min_time
    segment_len = experiment_len / args.segments

    port_ids = {}
    id = 0
    for port in relevant_interfaces.values():
        id += 1
        port_ids[port] = str(id)
    logging.info(port_ids)

    csv = create_sampling_csv(segment_len, args.segments, port_ids, time_to_samples, min_time, args.overload_byte_rate)

    csv_filename = pj(args.output_dir, "segments-decoded.csv")

    write_csv_to_file(csv_filename, csv)

if __name__ == '__main__':
    main()

