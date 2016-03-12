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
disregardCounter = ['sampleType_tag','sourceId', 'counterBlock_tag', 'networkType', 'ifSpeed', 'ifDirection', 'ifStatus', 'ifInBroadcastPkts','ifInUnknownProtos','ifOutMulticastPkts','ifOutBroadcastPkts','ifPromiscuousMode','ifInOctets','ifInUcastPkts']
relevantKeys = ['ifOutOctets','ifOutUcastPkts']
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


def create_sampling_csv(index_to_samples,sorted_if_names,destIfName,overloadByteRate):
    csv = ''
    for i in sorted(index_to_samples.keys(),key=int):
        values = []
        dest_delta = 0
        for eth in sorted_if_names:
            if eth == destIfName:
                dest_delta = int(get_delta(destIfName,i,index_to_samples,'ifOutOctets'))
                # don't output the destination port
                continue
            else:
                values.append(eth)
                values.append(index_to_samples[i][eth][timeKey])
                for k in relevantKeys:
                    values.append(index_to_samples[i][eth][k])
                    delta = get_delta(eth, i, index_to_samples, k)
                    values.append(delta)
        tag = '1' if dest_delta >= overloadByteRate else '0'
        logging.debug('tag='+tag)
        csv += ', '.join([tag] + values) + os.linesep
    return csv


def get_delta(eth, i, index_to_samples, k):
    curr = index_to_samples[i][eth][k]
    # insert delta for counter
    # (take delta from 0 if this is the first sample, or if the previous sample was lost somehow)
    if i == '1':
        delta = curr
    elif index_to_samples.has_key(str(int(i)-1)) == False:
        delta = curr
        logging.warn("Taking delta from 0 because the previous sample was not found for index %s"%i)
    else:
        delta = str(int(curr) - int(index_to_samples[str(int(i) - 1)][eth][k]))
    return delta


def filter_under_reported_indexes(index_to_samples, number_of_intfs):
    filtered_index_to_samples = {}
    for i in index_to_samples:
        if len(index_to_samples[i]) != number_of_intfs:
            logging.warn("Filtering samples of index %s, because it had %d samples (instead of # of ports = %d)"%(i,len(index_to_samples[i]),number_of_intfs))
            logging.info(index_to_samples[i])
        else:
            filtered_index_to_samples[i] = index_to_samples[i]
    return filtered_index_to_samples


def get_index_to_samples_map(datagrams, interfaces_to_names):
    index_to_samples = {}
    for d in datagrams:
        for s in d['samples']:
            # only accept counter samples which exist in the name mapping
            if s['sampleType'] == 'COUNTERSSAMPLE' and interfaces_to_names.has_key(s['ifIndex']):
                name = interfaces_to_names[s['ifIndex']]
                index = s['sampleSequenceNo']
                if not index_to_samples.has_key(index):
                    index_to_samples[index] = {name:get_relevant_sampling(s,d['unixSecondsUTC'])}
                else:
                    index_to_samples[index][name] = get_relevant_sampling(s,d['unixSecondsUTC'])
    return index_to_samples


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-dir", default="/tmp",
                        help="The directory where the interfaces and datagram log files can be found")
    parser.add_argument("-o", "--output-dir", default="/tmp",
                        help="The directory into which switch csv files will be written")
    parser.add_argument("-t","--threshold",default=0.76,type=float,help="Overload threshold percentage [0,1]")
    parser.add_argument("-b","--bandwidth",default=10,type=int,help="Link bandwidth [MB/s]")
    parser.add_argument("-d","--debug", action="store_true", help="Set verbosity to high (debug level)")
    args = parser.parse_args()
    args.overload_byte_rate = args.bandwidth * megaByte * args.threshold
    return args


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
    index_to_samples = get_index_to_samples_map(datagrams, relevant_interfaces)
    filtered_index_to_samples = filter_under_reported_indexes(index_to_samples, len(relevant_interfaces))
    sorted_if_names = sorted(relevant_interfaces.values())
    write_interface_csvs_to_files(filtered_index_to_samples, sorted_if_names, args.overload_byte_rate, args.output_dir)





if __name__ == '__main__':
    main()

