#!/usr/bin/python
import argparse
import logging
import json


SAME_KEY = 'SAME'
ASC_KEY = 'ASC'
DESC_KEY = 'DESC'


def get_interfaces_to_state_time_series(sax_filename):
    interfaces_time_series = {}
    with open(sax_filename) as inputFile:
        line = inputFile.readline()
        while not line == '':
            if not line.startswith('@NAME'):
                line = inputFile.readline()
                continue
            else:
                k = line.split('=')[1].strip()
                logging.info("key " + k + " detected")
                line = inputFile.readline()
                v = get_values_from_line(line,' -1')
                interfaces_time_series[k] = v
                line = inputFile.readline()
    return interfaces_time_series


def get_values_from_line(line, delim=' '):
    split = line.replace(' -2\n','').split(delim)
    return split


def get_interfaces_to_asc_desc_events(interfaces_to_state_time_series):
    new_map = {}
    keys_list = []
    for k,v in interfaces_to_state_time_series.items():
        new_map[k], keys = time_series_to_asc_desc_events(k,v)
        keys_list.extend(keys)
    return new_map, keys_list


def time_series_to_asc_desc_events(k, time_series):
    asc = k + ASC_KEY
    desc = k + DESC_KEY
    events = []
    prev = time_series[0]
    for e in time_series:
        if prev == e:
            events.append(SAME_KEY)
        elif prev > e:
            events.append(desc)
        else:
            events.append(asc)
    return events, [asc,desc]


def merge_asc_desc_events_to_single_timeline(interfaces_to_asc_desc_events):
    sorted_interface_names = sorted(interfaces_to_asc_desc_events.keys())
    timeline = []
    for i in xrange(len(interfaces_to_asc_desc_events[sorted_interface_names[0]])):
        for k in sorted_interface_names:
            value = interfaces_to_asc_desc_events[k][i]
            if not value == SAME_KEY:
                timeline.append(value)
    return timeline


def encode_asc_desc_timeline(asc_desc_events_timeline, interfaces_asc_desc_events_to_integers):
   encoded_timeline = []
   for e in asc_desc_events_timeline:
       encoded_timeline.append(interfaces_asc_desc_events_to_integers[e])
   return encoded_timeline


def encode_timeline(asc_desc_events_timeline, interfaces_asc_desc_events_to_integers):
    encoded_timeline = [str(interfaces_asc_desc_events_to_integers[e]) for e in asc_desc_events_timeline]
    return encoded_timeline


def split_timeline_in_equal_parts(asc_desc_events_timeline, parts):
    length = len(asc_desc_events_timeline)
    n = length / parts
    split_timeline = [asc_desc_events_timeline[i:i + n] for i in xrange(0, length, n)]
    return split_timeline


def create_event_streams_in_spmf_format(event_streams):
    spmf_str = ''
    curr = 1
    for s in event_streams:
        stream_str = '@NAME=STREAM' + str(curr) + '\n'
        curr += 1
        stream_str += ' -1 '.join(s) + ' -1 -2 \n'
        spmf_str += stream_str
    return spmf_str


def write_event_streams_to_file(event_streams, filename):
    event_streams = create_event_streams_in_spmf_format(event_streams)
    logging.info("Writing event streams to " + filename)
    logging.debug(event_streams)
    with open(filename,'w') as f:
        f.write(event_streams)


def write_event_encoding_to_file(interfaces_asc_desc_events_to_integers, events_encoding_filename):
    logging.info("Writing event encodings to " + events_encoding_filename)
    with open(events_encoding_filename,'w') as f:
        json.dump(interfaces_asc_desc_events_to_integers,f)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True,
                        help="The file containing SAX output")
    parser.add_argument("-s", "--streams_filename", required=True,
                        help="The filename into which the SAX combined data will be written")
    parser.add_argument("-e", "--events-encoding_filename", required=True,
                        help="The filename into which the events encoding will be written")
    parser.add_argument("-p","--parts", type=int, default=4, help="Set amount of parts to output timeline in - should be positive")
    parser.add_argument("-d","--debug", action="store_true", help="Set verbosity to high (debug level)")
    args = parser.parse_args()
    assert args.parts > 0
    return args


def main():
    args = parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    interfaces_to_state_time_series = get_interfaces_to_state_time_series(args.input)

    interfaces_to_asc_desc_events, interfaces_asc_desc_events_list = get_interfaces_to_asc_desc_events(interfaces_to_state_time_series)
    asc_desc_events_timeline = merge_asc_desc_events_to_single_timeline(interfaces_to_asc_desc_events)

    interfaces_asc_desc_events_to_integers = {k: v for v, k in enumerate(interfaces_asc_desc_events_list)}
    encoded_timeline = encode_timeline(asc_desc_events_timeline, interfaces_asc_desc_events_to_integers)

    event_streams = split_timeline_in_equal_parts(encoded_timeline, args.parts)

    write_event_streams_to_file(event_streams, args.streams_filename)
    write_event_encoding_to_file(interfaces_asc_desc_events_to_integers, args.events_encoding_filename)


if __name__ == '__main__':
    main()

