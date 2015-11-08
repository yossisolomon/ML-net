#!/usr/bin/python


def map_interfaces():


startDatagram ='startDatagram ================================='
endDatagram ='endDatagram ================================='
def map_datagrams():
    datagrams = []
    with open('/tmp/sflow-datagrams') as file:
        line = file.readline()
        while not line == '':
            if line == startDatagram:
                datagrams.append(get_datagram_map(file))
            line = file.readline()
            
def get_datagram_map(file):
    l = file.readline()
    while not l = endDatagram:
        
        l = file.readline()

def main():
    interfaces = map_interfaces()
    datagrams = map_datagrams()
    create_interface_csv_files()
            

if __name__ == '__main__':
    main()

