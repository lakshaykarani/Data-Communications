#Author: Lakshay Karani lakshay.karani@colorado.edu
#Distributed File System Contents: DFS.py, /DFS1, /DFS2, /DFS3, /DFS4, dfs.conf , DFC.py, dfc.conf
#purpose: To Create a distributed file system for reliable and secure file storage.
#Python version: 3.5.1

DISTRIBUTED FILE SYSTEM:

A Distributed File System is a client/server-based application that allows a client to store and retrieve files on multiple servers.
One of the features of Distributed file system is that each file can be divided in to pieces and stored on different servers.


BEFORE RUNNING THE DFS SERVERS AND DFC CLIENT:

o Make sure dfc.conf file has the DFS Server Information and a Username Password for the client:

			Server DFS1 127.0.0.1:9001
			Server DFS2 127.0.0.1:9002
			Server DFS3 127.0.0.1:9003
			Server DFS4 127.0.0.1:9004
			Username: Lakshay
			Password: DFSystem
			
o Make sure dfs.conf is present in all DFS Directories i.e. /DFS1 to /DFS4 and it contains Username Password information for the all the clients:
			[User] [Password]
			Lakshay DFSystem
			John Pass123
			
o To run the Client : dfc.py dfc.conf

o To run the Server : dfs.py /DFS[1-4] [PortNumber]

o Create a directory /DFC and place all the files that you want to send to the server.

o Before running the Client Program, make sure servers are up and running.

o After the client is executed, the program will first authenticate the user.

o List of options available for a user:

	- GET [Filename]		:This option is used to get all the parts of a particular file from the required servers.
	- PUT [Filename]		:This option breaks the specified file into chunks and stores them in different servers.
	- LIST					:This option lists all the files available for a particular user and also specifies if the file can be successfully regenerated. 
							 If not the file is marked with an [Incomplete Label]
	- MKDIR					:This option is used to create a blank directory on the servers.

FEATURES OF DISTRIBUTED FILE SYSTEM:

o The DFC splits the file into 4 pieces and groups them into 4 pairs(P1, P2), (P2, P3),(P3, P4),(P4, P1). 
  These groups are then uploaded onto 4 DFS servers based on the MD5 Hash Value.
o There will be a User Directory under every /DFS Servers which will contain user specific files and folders.
o The file is encrypted using Simple-Crypt Module before the pieces are sent to the servers.
o Since there are 2 copies of each piece getting stored on to the servers, there is traffic optimization in place which will only fetch the required pieces to regenerate the file.
o Upgraded options with Sub Folder Functionality

 

