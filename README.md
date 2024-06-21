## Network Emulator
- Developed by Sri Sai Ram Kiran Muppana & Sahithi Vungarala for the course DATA/COMPUTER COMMUNICATIONS (CNT5505-01.sp09), Computer Science, FSU


- Author/email address

	SM22BT  - Sri Sai Ram Kiran Muppana \
    SV22N   - Sahithi Vungarala

- Platform type: linux

- Commands supported in stations/routers/bridges

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


- To start the emulation, run

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


- Difficulties that we have encountered during the development of the project

    - When the pending queue had more than 5 IP packets, not all packets were reaching the destination. Interestingly, only packets at even positions were received. This posed a dilemma, and initially, we were unable to identify the issue. Later, we discovered that the problem was related to the receiver buffer size at the station. After increasing the buffer size, the issue was resolved.

- A LOG of the progress we make from time to time
	
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
