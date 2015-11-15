#!/usr/bin/python

import os
from datetime import datetime
import logging

pj = os.path.join

baseFolder = pj('/tmp')
startDatagram ='startDatagram =================================\n'
endDatagram ='endDatagram   =================================\n'
startSample = 'startSample ----------------------\n'
endSample = 'endSample   ----------------------\n'
disregardCounter = ['sampleType_tag','sourceId', 'counterBlock_tag', 'networkType', 'ifSpeed', 'ifDirection', 'ifStatus', 'ifInBroadcastPkts','ifInUnknownProtos','ifOutMulticastPkts','ifOutBroadcastPkts','ifPromiscuousMode']
relevantKeys = ['ifInOctets','ifInUcastPkts','ifOutOctets','ifOutUcastPkts']
loadersIfNames = ['s0-eth1','s1-eth1','s2-eth1']
destIfName = 's3-eth1'
deltasErrorMargin = 0.05
mega = pow(2,20)
megaByte = mega/8
overloadByteRate = 10*megaByte*0.7


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


def get_relevant_sampling(sample):
    new_sample = {}
    for k in relevantKeys:
        new_sample[k] = sample[k]
    return new_sample


def is_sampling_size_ok(index_to_samples):
    sampling_counters = [len(s) for s in index_to_samples.values()]
    if len(set(sampling_counters)) > 1:
        return False
    return True


def is_deltas_sampling_ok(loaders_tot_delta,dest_delta):
    if abs(loaders_tot_delta-dest_delta) > deltasErrorMargin*dest_delta:
        return False
    return True


def create_sampling_csv_file(index_to_samples,sorted_if_names):
    with open(pj(baseFolder,'sflowCSV-%s'%datetime.now().isoformat()),'w') as f:
        for i in sorted(index_to_samples.keys()):
            values = []
            loaders_tot_delta = 0
            dest_delta = 0
            for eth in sorted_if_names:
                for k in relevantKeys:
                    values.append(index_to_samples[i][eth][k])
                    curr = index_to_samples[i][eth][k]
                    # insert delta for counter
                    # (take delta from 0 if this is the first sample)
                    delta = curr if i=='1' else str(int(curr)-int(index_to_samples[str(int(i)-1)][eth][k]))
                    if eth in loadersIfNames and k == 'ifInOctets':
                        logging.info("delta for " + eth + " :" + delta)
                        loaders_tot_delta += int(delta)
                    elif eth == destIfName and k == 'ifOutOctets':
                        dest_delta = int(delta)
                    values.append(delta)
            tag = '1' if loaders_tot_delta >= overloadByteRate else '0'
            if not is_deltas_sampling_ok(loaders_tot_delta,dest_delta):
                logging.warn('Deltas margin of error (%s) passed for sample#%s: loadTot=%s   dest=%s'%(deltasErrorMargin,i,loaders_tot_delta,dest_delta))
            logging.info('tag='+tag)
            f.write(', '.join([tag] + values) + os.linesep)


def get_index_to_samples_map(datagrams, interfaces_to_names):
    index_to_samples = {}
    for d in datagrams:
        for s in d['samples']:
            # only accept counter samples which exist in the name mapping
            if s['sampleType'] == 'COUNTERSSAMPLE' and interfaces_to_names.has_key(s['ifIndex']):
                name = interfaces_to_names[s['ifIndex']]
                index = s['sampleSequenceNo']
                if not index_to_samples.has_key(index):
                    index_to_samples[index] = {name:get_relevant_sampling(s)}
                else:
                    index_to_samples[index][name] = get_relevant_sampling(s)
    return index_to_samples


def main():
    logging.info("overload th: " + str(overloadByteRate))
    interfaces_to_names = get_interfaces_to_names_map()
    relevant_interfaces = dict(filter(lambda (i,n): "-eth" in n and not "root" in n,interfaces_to_names.items()))
    datagrams = get_datagrams()
    index_to_samples = get_index_to_samples_map(datagrams, relevant_interfaces)
    if not is_sampling_size_ok(index_to_samples):
        raise Exception("bad sampling")
    sorted_if_names = sorted(relevant_interfaces.values())
    create_sampling_csv_file(index_to_samples,sorted_if_names)


if __name__ == '__main__':
    main()

