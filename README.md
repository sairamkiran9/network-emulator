#############################################################################
# Developped by Sri Sai Ram Kiran Muppana & Sahithi Vungarala for the course
#
# DATA/COMPUTER COMMUNications (CNT5505-01.sp09)  
# Computer Science, FSU
#############################################################################


1. Author/email address

	SM22BT  - Sri Sai Ram Kiran Muppana
    SV22N   - Sahithi Vungarala

2. Platform type: linux

3. Commands supported in stations/routers/bridges

   3.1 stations:

	   send <destination> <message>     // send message to a destination host
	   show arp 		                // show the ARP cache table information
	   show pq 		                    // show the pending_queue
	   show	host 		                // show the IP/name mapping table
	   show	iface 		                // show the interface information
	   show	rtable 		                // show the contents of routing table
	   quit                             // close the station

   3.2 routers:

	   show	arp 		                // show the ARP cache table information
	   show	pq 		                    // show the pending_queue
	   show	host 		                // show the IP/name mapping table
	   show	iface 		                // show the interface information
	   show	rtable 		                // show the contents of routing table
	   quit                             // close the router


   3.3 bridges:

	   show sl 		                    // show the contents of self-learning table
	   quit                             // close the bridge


4. To start the emulation, run

   	run_simulation

   , which emulates the following network topology

   
          B              C                D
          |              |                |
         cs1-----R1------cs2------R2-----cs3
          |              |                |
          -------A--------                E

    cs1, cs2, and cs3 are bridges.
    R1 and R2 are routers.
    A to E are hosts/stations.
    Note that A is multi-homed, but it is not a router.


5. Difficulties that we have encountered during the development of the project

    - Pending queue, when there were more than 5 ip-packets in the queue, not all packets are received at the destination. More interestingly only packets at even positions are received. So got into a dilemma and not able to figure out the issue. After ____ we are able to figure out that it's because of receiver buffer size in station. After increasing the buffer size the issue is resolved.

6. A LOG of the progress we make from time to time
	
	- Creating project folder structure
    - Creating bridge class to save primary details => take input arguments and save to class object
    - initializing socket and creating a symbolic link
    - creating station class to save primary details => take input arguments and save to class object
    - read and load ifaces and rtable files
    - adapt project1 into this i.e implement client-server program to broadcast msgs
    - Now based on the symlink data connect station to bridge
    - ensure broadcasting msg is working
    - now create encapsulated data frame, pending queue class to store ip-packet
    - nexthop calculation 
    - implement arp protocol mechanism
    - router forwarding and show, quit commands
    - signal handling in bridge and station
    - retry mechanism to check connection
