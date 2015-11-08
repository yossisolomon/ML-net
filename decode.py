#!/usr/bin/python


def get_interfaces_to_names_map():
    interfaces = {}
    with open('/tmp/intfs-list') as inputFile:
        line = inputFile.readline()
        while not line == '':
            k,v = get_key_value_from_line(line,': ')
            interfaces[k] =v
            line = inputFile.readline()
    return interfaces



startDatagram ='startDatagram ================================='
endDatagram ='endDatagram ================================='
def get_datagrams():
    datagrams = []
    with open('/tmp/sflow-datagrams') as inputFile:
        line = inputFile.readline()
        while not line == '':
            if line == startDatagram:
                datagrams.append(get_datagram_map(inputFile))
            line = inputFile.readline()
    return datagrams

startSample = 'startSample ----------------------'
endSample = 'endSample ----------------------'
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
        sample[k] = v
        l = inputFile.readline()
    return sample

def get_key_value_from_line(line, delim=' '):
    split = line.split(delim)
    return split[0] , split[1]

def create_interface_csv_files(interfaces_to_names, datagrams):
    names_to_samples = {}
    for d in datagrams:
        for s in d['samples']:
            name = interfaces_to_names[s['ifIndex']]
            if names_to_samples[name] is None:
                names_to_samples[name] = [s]
            else:
                names_to_samples[name].append(s)
    for name, samples in names_to_samples.iteritems():
        with open('/tmp/sflowCSV-'+name) as f:
            for s in samples:
                f.write(', '.join(s))



def main():
    interfaces_to_names = get_interfaces_to_names_map()
    datagrams = get_datagrams()
    create_interface_csv_files(interfaces_to_names, datagrams)


if __name__ == '__main__':
    main()

