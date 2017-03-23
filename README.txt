============== UDP FILE TRANSFER PROGRAM ===================

A program to transfer files in between Client and Server. Use PYTHON 3.5 to compile and run this program.
UDP_Client.py takes a command line argument including the Port number - in between 5000 - 65535 and Server IP address; in this case you can use 127.0.0.1.
UDP_Server.py takes in only the port number which should be in between 5000 - 65535.

UDP_Client.py takes a command from the user to perform a particular opertion as explained below. The script can be used to transfer and receive large files.

The program initially sends the header information containing the specific command and filenames. Then it reads data in sequential order of 1024 bytes. 
These data or packets are sent over the network and is received sequentially on the other side. This sequential data is then combined and written onto to the file.

Steps to follow to run the program

Before running the program:

o Make sure the UDP_Client.py is not inside the Client folder. Client Folder is used to store, transfer and receive files from the server.

o There are 4 files in the Client folder are foo1.txt, foo2.jpg, foo3.zip, foo4.jpg, foo5.txt, Dog.mp4. You are free to try any kind of a file. Hopefully it should work. 

During the program:

o Make sure you run the UDP_Server.py before sending any data. Run the program as UDP_Server.py PORT NUMBER. Port Number should be in between 5000 and 65535.
  
o Run the UDP_Client.py as UDP_Client.py SERVER_IP[X.X.X.X] PORT NUMBER.

o UDP_Server.py will just listen to any incoming message and give a reply to the host.

o There are 4 Commands that you can give to UDP_Client to process any data:
	
	- put [file_name] : This command will transfer the file as specified by the Client to the Server. The file to be sent should be placed in the Client/ directory.
	- get [file_name] : This command will first check if the file is present in the server. If not the server will send an error message to the client saying "File not available". 
						Otherwise the server will transfer the file and store it in Client/ folder.
	- list			  : This command will list all the files present in the Server Directory.
	- exit			  : This command will cause the Server to shut down and also will exit from the Client Program.

