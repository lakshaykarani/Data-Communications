#!/usr/bin/env python3
#author: Lakshay Karani lakshay.karani@colorado.edu
#name: UDP_Client.py
#purpose: To tranfer and receive files using UDP
#python version:3.5


import argparse, socket
import os, re, sys, time
MaxBytes = 1024

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(20)


#INITIALIZING COMMAND LINE ARGUMENTS
def initializeParser():
    parser = argparse.ArgumentParser(description='UDP Client')
    parser.add_argument('s', metavar='ServerAddress', help = "Server IP Address (ex = 127.0.0.1)")
    parser.add_argument('p', metavar='PortNumber', type=int, help='UDP Port (ex = 5001)')
    args = parser.parse_args()
    if args.p < 5000 or args.p > 65535:
        print("ERROR: Invalid Port Number. Please enter Port Number in between 5000 and 65535")
        print("Program Terminated")
        sys.exit()
    return args

#SENDING HEADER INFORMATION AND RECIEVING STATUS
def sendRxStatus(fileHeader, server, port):

    text = fileHeader.encode('ASCII')
    sock.sendto(text, (server, port))
    try:
        text, address = sock.recvfrom(MaxBytes)
        status = text.decode('ASCII')
        print("\nReply from the server {} : {!r}".format(address, status))

    except socket.timeout as e:
        print("Server ", e)
        print("Server Down! Try again.")
        main()

       
    return status


#GETTING FILE FROM SERVER
def getFile(file_name,server, port):
    
    fileHeader = "get"+"||"+file_name
    
    status = sendRxStatus(fileHeader, server, port)   #Sending header and receiving status

    try:
        text, address = sock.recvfrom(MaxBytes)
        status = text.decode('ASCII')
        print("\nReply from the server {} : {!r}".format(address, status))

    except socket.timeout as e:
        print("Server ", e)
        print("Server Down! Try again.")
        main()
    except UnicodeDecodeError:
        print("SYNC ERROR: Couldn't find a string to decode! Try Again!")
        main()


    if status == "ERROR: File not found.":
        main()
            
    if not os.path.exists("Client"):
        os.makedirs("Client")


    firstPacket = True
    packetArray = []
    while True:
        #Receiving Packets from the server 
        rxContent, address = sock.recvfrom(MaxBytes)
        if firstPacket == True and rxContent != b'':
            text = "SUCCESS: First packet received from {} . Acknowledging to send the entire data".format(address)
            data = text.encode('ASCII')
            sock.sendto(data, address)                
            print("\nTransfer in Progress.....")
            firstPacket = False
       
        if rxContent == b'||EOF||':
            break
       
        packetArray.append(rxContent)
    recoveredFile = b''.join(packetArray)
    
    fileNameRx = "Client/recieved_" + file_name
    fileHandle = open(fileNameRx, 'wb')
    fileHandle.write(recoveredFile)
    fileHandle.close()
    
    print("\nTransfer Status : File Received".format(address))
    print("\nThe file transfer was {} bytes long." .format(len(recoveredFile)))
    


#Putting files onto the server    
def putFile(file_name,server, port):

    fileHeader = "put"+"||"+file_name
    
    dirFileName = "Client/"+file_name

    if os.path.isfile(dirFileName):
        status = sendRxStatus(fileHeader, server, port)
        firstPacket = True
        with open(dirFileName, 'rb') as fileHandle:
            while True:
                #Reading packets of 1024 bytes and transmitting to the server
                packet = fileHandle.read(MaxBytes)    
                if packet:
                    sock.sendto(packet, (server, port))
                    time.sleep(0.001)
                    if firstPacket == True:
                        print("\nWaiting for the server to acknowledge the first Packet")
                        ack, address = sock.recvfrom(MaxBytes)
                        if re.match("SUCCESS", ack.decode('ASCII')):
                            print("\nReply from server {}: {}".format(address, ack.decode('ASCII')))
                            print("\nTransfer in Progress.....")
                            firstPacket = False
                        else:
                            print("\nFile Transfer Failed. Try Again")
                            main()
                else:
                    text = b'||EOF||'
                    sock.sendto(text, (server, port))
                    break

        fileHandle.close()        
     
        try:
            text, address = sock.recvfrom(MaxBytes)
            status = text.decode("ASCII")
            print("\nReply from the server {} : {}".format(address, status))
        except socket.timeout as e:
            print("Server ", e)
            print("Server Down! Try again.")
            main()
    
    
    else:
        print("ERROR: File "+file_name+" not found in the Client/ directory.")
        main()

#Getting the file list from the server
def getList(server, port):

    fileHeader = "list" +"||"+"list"
    status = sendRxStatus(fileHeader, server, port)
    if re.match(status, "ERROR" , re.IGNORECASE):
        sys.exit()

    
    try:
        listFiles, address = sock.recvfrom(MaxBytes)
    except socket.timeout as e:
        print("Server ", e)
        print("Server Down! Try again.")
        main()


    text = listFiles.decode("ASCII")
    print("\nList of files available in the server {} :\n{}".format(address, text))

def main():
    try:
        hostServer = initializeParser()
        prompt = "> "
        while True:
            print('='*50)
            print("UDP File Transfer Program: ")
            print('='*50)
            print("""\n\
            Choose an operation:\n\
            o get [file_name]\n\
            o put [file_name]\n\
            o list\n\
            o exit\n\
            """)
            try:
                choice = input(prompt).split()
            except EOFError:
                print("Program Terminated")
                sys.exit()
            #Verifying the Command entered by the user
            if choice[0] == "get":
                if len(choice) != 2:
                    print ("\nERROR: Please enter the command as : get [file_name]")
                else:    
                    getFile(choice[1],hostServer.s, hostServer.p)
            
            elif choice[0] == "put":
                if len(choice) != 2:
                    print ("\nERROR: Please enter the command as : put [file_name]")
                else:    
                    putFile(choice[1], hostServer.s, hostServer.p)
                
            elif choice[0] == "list":
                if len(choice) != 1:
                    print ("\nERROR: Please enter the command as : list")
                else:    
                    getList(hostServer.s, hostServer.p)
            
            elif choice[0] == "exit":
                if len(choice) != 1:
                    print ("\nERROR: Please enter the command as : exit")
                else:    
                    while True:
                        print("\nAre you sure to exit? [y/n]")
                        exitFlag = input(prompt).split()
                        if exitFlag[0] == 'y' or exitFlag[0] =='Y':
                            
                            print("\nThank you for using UDP File Tranfer Program.")
                            fileHeader = choice[0] 
                            text = fileHeader.encode('ASCII')    
                            sock.sendto(text, (hostServer.s, hostServer.p))

                            sys.exit()
                        elif exitFlag[0] == 'n' or exitFlag[0] =='N':
                            break
                        else:
                            print("\nInvalid option. Please enter the correct option")
                        
            else:
                fileHeader = choice[0]
                sendRxStatus(fileHeader, hostServer.s, hostServer.p)
                try:
                    text, address = sock.recvfrom(MaxBytes)
                except socket.timeout as e:
                    print("Server ", e)
                    print("Server Down! Try again.")
                    main()
            
                status = text.decode('ASCII')
                print("\nReply from the server {} :\n{!r}".format(address, status))
                
                print("\nInvalid command. Please enter the correct command as specified")        

    except KeyboardInterrupt as e:
        print("Keyboard Interrupt: Program Terminated")
        sock.close()
        sys.exit()
    except ConnectionResetError as e:
        print(e)
        print("Server Down! Try again.")
        main()
    except IndexError:
        print("ERROR: Please enter a Valid Command!")
        main()
    finally:
        sock.close()
        sys.exit()

if __name__ == '__main__' : main()
