#!/usr/bin/python

import os
import time
import logging

pj = os.path.join

baseFolder = pj(os.sep,'tmp')
startDatagram ='startDatagram =================================\n'
endDatagram ='endDatagram   =================================\n'
startSample = 'startSample ----------------------\n'
endSample = 'endSample   ----------------------\n'
disregardCounter = ['sampleType_tag','sourceId', 'counterBlock_tag', 'networkType', 'ifSpeed', 'ifDirection', 'ifStatus', 'ifInBroadcastPkts','ifInUnknownProtos','ifOutMulticastPkts','ifOutBroadcastPkts','ifPromiscuousMode']
relevantKeys = ['ifInOctets','ifInUcastPkts','ifOutOctets','ifOutUcastPkts']
timeKey = 'time'
destIfName = 's3-eth1'
deltasErrorMargin = 0.15
mega = pow(2,20)
megaByte = mega/8
overloadByteRate = 10*megaByte*0.76


def get_interfaces_to_names_map():
    interfaces = {}
    with open(pj(baseFolder,'intfs-list')) as inputFile:
        line = inputFile.readline()
        while not line == '':
            k,v = get_key_value_from_line(line,': ')
            interfaces[k] =v
            line = inputFile.readline()
    return interfaces


def get_datagrams():
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


def is_sampling_size_ok(index_to_samples):
    sampling_counters = [len(s) for s in index_to_samples.values()]
    if len(set(sampling_counters)) > 1:
        return False
    return True


def create_sampling_csv_file(index_to_samples,sorted_if_names):
    out_file = pj(baseFolder,'sflowCSV-%s'%time.strftime("%Y%m%d-%H%M%S"))
    with open(out_file,'w') as f:
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
            logging.info('tag='+tag)
            f.write(', '.join([tag] + values) + os.linesep)
    return out_file


def get_delta(eth, i, index_to_samples, k):
    curr = index_to_samples[i][eth][k]
    # insert delta for counter
    # (take delta from 0 if this is the first sample)
    delta = curr if i == '1' else str(int(curr) - int(index_to_samples[str(int(i) - 1)][eth][k]))
    return delta


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


def main():
    #logging.getLogger().setLevel(logging.INFO)
    logging.info("overload th: " + str(overloadByteRate))
    interfaces_to_names = get_interfaces_to_names_map()
    relevant_interfaces = dict(filter(lambda (i,n): "-eth" in n and not "root" in n,interfaces_to_names.items()))
    datagrams = get_datagrams()
    index_to_samples = get_index_to_samples_map(datagrams, relevant_interfaces)
    if not is_sampling_size_ok(index_to_samples):
        raise Exception("bad sampling")
    sorted_if_names = sorted(relevant_interfaces.values())
    out_file = create_sampling_csv_file(index_to_samples,sorted_if_names)
    logging.info("The output file is: %s"%out_file)

if __name__ == '__main__':
    main()

