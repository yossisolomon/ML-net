#!/usr/bin/python

"""
"""
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import Node
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.util import dumpNodeConnections

class GeneratedTopo( Topo ):

    def __init__( self, **opts ):
        "Create a topology."

        # Initialize Topology
        Topo.__init__( self, **opts )

        # add nodes, switches first...
        NewYork = self.addSwitch( 's0' )
        Chicago = self.addSwitch( 's1' )
        WashingtonDC = self.addSwitch( 's2' )
        Seattle = self.addSwitch( 's3' )
        Sunnyvale = self.addSwitch( 's4' )
        LosAngeles = self.addSwitch( 's5' )
        Denver = self.addSwitch( 's6' )
        KansasCity = self.addSwitch( 's7' )
        Houston = self.addSwitch( 's8' )
#        Atlanta = self.addSwitch( 's9' )
#        Indianapolis = self.addSwitch( 's10' )

        # ... and now hosts
        NewYork_host = self.addHost( 'h0' )
        Chicago_host = self.addHost( 'h1' )
        WashingtonDC_host = self.addHost( 'h2' )
        Seattle_host = self.addHost( 'h3' )
        Sunnyvale_host = self.addHost( 'h4' )
        LosAngeles_host = self.addHost( 'h5' )
        Denver_host = self.addHost( 'h6' )
        KansasCity_host = self.addHost( 'h7' )
        Houston_host = self.addHost( 'h8' )
#        Atlanta_host = self.addHost( 'h9' )
#        Indianapolis_host = self.addHost( 'h10' )


        # add edges between switch and corresponding host
        self.addLink( NewYork , NewYork_host )
        self.addLink( Chicago , Chicago_host )
        self.addLink( WashingtonDC , WashingtonDC_host )
        self.addLink( Seattle , Seattle_host )
        self.addLink( Sunnyvale , Sunnyvale_host )
        self.addLink( LosAngeles , LosAngeles_host )
        self.addLink( Denver , Denver_host )
        self.addLink( KansasCity , KansasCity_host )
        self.addLink( Houston , Houston_host )
#        self.addLink( Atlanta , Atlanta_host )
#        self.addLink( Indianapolis , Indianapolis_host )

        # add edges between switches
        self.addLink( NewYork , Sunnyvale, bw=10, delay='10ms')
        #self.addLink( NewYork , WashingtonDC, bw=10, delay='1s')
        self.addLink( Chicago , Denver, bw=10, delay='10ms')
        self.addLink( Houston , Seattle, bw=10, delay='10ms')
        self.addLink( LosAngeles , Sunnyvale, bw=10, delay='10ms')
        #self.addLink( Seattle , Denver, bw=10, delay='1s')
        #self.addLink( Sunnyvale , LosAngeles, bw=10, delay='2.55695492867ms')
        #self.addLink( Sunnyvale , Denver, bw=10, delay='7.64100479966ms')
        self.addLink( Houston , WashingtonDC, bw=10, delay='10ms')
        self.addLink( Denver , KansasCity, bw=10, delay='10ms')
        self.addLink( KansasCity , Houston, bw=10, delay='10ms')
        #self.addLink( KansasCity , Indianapolis, bw=10, delay='3.7130222434ms')
        self.addLink( Houston , LosAngeles, bw=10, delay='10ms')
        #self.addLink( Atlanta , Indianapolis, bw=10, delay='3.49428237002ms')

topos = { 'generated': ( lambda: GeneratedTopo() ) }

# HERE THE CODE DEFINITION OF THE TOPOLOGY ENDS

# the following code produces an executable script working with a remote controller
controller_ip = '10.0.3.11'
#controller_ip = ''

def setupNetwork(controller_ip):
    #Create network
    topo = GeneratedTopo()
    # check if remote controller's ip was set
    # else set it to localhost
    if controller_ip == '':
        controller_ip = '127.0.0.1';
    net = Mininet(topo=topo, controller=lambda a: RemoteController( a, ip=controller_ip, port=6633 ), link=TCLink)
    #adds root for ssh + starts net
    connectToRootNS(net)
    return net


def connectToRootNS( network, ip='10.123.123.1', prefixLen=8, routes=['10.0.0.0/8'] ):
    "Connect hosts to root namespace via switch. Starts network."
    "network: Mininet() network object"
    "ip: IP address for root namespace node"
    "prefixLen: IP address prefix length (e.g. 8, 16, 24)"
    "routes: host networks to route to"
    switch = network.switches[0]
    # Create a node in root namespace and link to switch 0
    root = Node( 'root', inNamespace=False )
    intf = TCLink( root, switch ).intf1
    root.setIP( ip, prefixLen, intf )
    # Start network that now includes link to root namespace
    network.start()
    # Add routes from root ns to hosts
    for route in routes:
        root.cmd( 'route add -net ' + route + ' dev ' + str( intf ) )


def setupITG( network ):
    for host in network.hosts:
        host.cmd( '/usr/sbin/sshd -D &')
        host.cmd( 'ITGRecv < /dev/null &' )

    # DEBUGGING INFO
    print
    print "Dumping host connections"
    dumpNodeConnections(network.hosts)
    print
    print "*** Hosts addresses:"
    print
    for host in network.hosts:
        print host.name, host.IP()
    print
    print "*** Type 'exit' or control-D to shut down network"
    print
    print "*** For testing network connectivity among the hosts, wait a bit for the controller to create all the routes, then do 'pingall' on the mininet console."
    print

    CLI( network )
    print "Killing ITGRecv(s)..."
    for host in network.hosts:
        host.cmd('kill %' + '/usr/sbin/sshd')
        host.cmd( 'pkill -15 ITGRecv')
    print "Stopping the network..."
    network.stop()


if __name__ == '__main__':
    setLogLevel('info')
    #setLogLevel('debug')
    setupITG( setupNetwork(controller_ip) )
