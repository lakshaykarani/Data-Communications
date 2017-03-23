#!/usr/bin/env python3
#author: Lakshay Karani lakshay.karani@colorado.edu
#name: UDP_Server.py
#purpose: To tranfer and receive files using UDP
#python version:3.5

import argparse, socket, sys, os, re, time
MaxBytes = 1024
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#Receive the Command and send the status information
def sendRxStatus(sock):

    try:
        text, address = sock.recvfrom(MaxBytes)
        fileHeader = text.decode('ASCII')    
        text = "Connection Established with server {}".format(sock.getsockname())
        data = text.encode('ASCII')
        sock.sendto(data, address)

    except socket.timeout as e:
        print("\nServer ", e)
        print("\nServer Down! Try again.")
        main()
       
    return fileHeader, address

#Main loop for the server to listen
def serverListen(port):

    sock.bind(("",port))
    
    
    while True:
        print("\nListening at {}".format(sock.getsockname()))
        fileHeaderRx, address = sendRxStatus(sock)

        header = fileHeaderRx.split("||")        
        #If the command entered by the user is PUT
        if header[0] == 'put':
            print("\nIncoming message from client {} : Operation to {!r} {}".format(address, header[0], header[1]))
        
            if not os.path.exists("Server"):
                os.makedirs("Server")            
            packetArray = []
            firstPacket = True
            while True:
                #Receiving Packets from Client and regenerating the file
                rxContent, address = sock.recvfrom(MaxBytes)
                if firstPacket == True and rxContent != b'':
                    text = "SUCCESS: First packet received from {} . Acknowledging to send the entire data".format(address)
                    print("\nFirst packet received. Sending Acknowledgement")
                    data = text.encode('ASCII')
                    sock.sendto(data, address)                
                    print("\nTransfer in Progress.....")
                    firstPacket = False
                
                if rxContent == b'||EOF||':
                    break
                packetArray.append(rxContent)
            recoveredFile = b''.join(packetArray)

            fileNameRx = "Server/recieved_" + header[1]            
            fileHandle = open(fileNameRx, 'wb')
            fileHandle.write(recoveredFile)
            fileHandle.close()
            
            print("\nTransfer completed successfully!")
            text = "File Transfer Complete.Your data was {} bytes long." .format(len(recoveredFile))
           
            data = text.encode('ASCII')
            sock.sendto(data, address)                
    
                        
        #If command entered by the user is GET    
        elif header[0] == 'get':

            fileNameRx = "Server/recieved_" + header[1]
            print("\nIncoming message from client {} : Operation to {!r} {}".format(address, header[0], header[1]))
            
            
            if os.path.isfile(fileNameRx):
                print("\nAttempting to transfer file : {} ".format(fileNameRx))
                text = "File "+header[1]+" is Available at {} . Initiating transfer. ".format(sock.getsockname())
                data = text.encode('ASCII')
                sock.sendto(data, address)

                #Making packets of the data and sending it to the client
                firstPacket = True
                with open(fileNameRx, 'rb') as fileHandle:
                    while True:
                        packet = fileHandle.read(MaxBytes)    
                        if packet:
                            sock.sendto(packet, address)
                            time.sleep(0.001)
                            if firstPacket == True:
                                print("\nWaiting for the client to acknowledge the first Packet")
                                ack, address = sock.recvfrom(MaxBytes)
                                if re.match("SUCCESS", ack.decode('ASCII')):
                                    print("\nReply from client {}: {}".format(address, ack.decode('ASCII')))
                                    print("\nTransfer in Progress.....")
                                    firstPacket = False
                                else:
                                    print("File Transfer Failed. Try Again")
                                    main()
                                    
                        else:
                            text = b'||EOF||'
                            sock.sendto(text, address)
                            break
                
                fileHandle.close()
                
                print("\nFile {} transferred from {} to {}" .format(header[1], sock.getsockname(), address))

            else:
                text = "ERROR: File not found."
                print(text)
                data = text.encode('ASCII')
                sock.sendto(data, address)
        #If the command from the user is LIST
        elif header[0] == 'list':
            
            print("\nIncoming message from client {} : Operation to {!r} all files in the server".format(address, header[0]))
            if os.path.exists("Server/"):
                serverPath = "Server/"                
                dirs = os.listdir(serverPath)
                dirs = [line.strip("received_") for line in dirs]

                listFiles = '\n'.join(dirs)
                print("\nList of files available:\n{}".format(listFiles))
                sock.sendto(listFiles.encode("ASCII"), address)
                print("\nTransferring list to {}" .format(  address))
            else:
                print("Server Folder Does not exist")
                text= "The Server Folder does not exist. Kindly put some files onto the server"
                sock.sendto(text.encode("ASCII"), address)
        #Exit will cause the Server to Shut Down        
        elif header[0] == 'exit':
            print("\nServer Shut Down!")
            sys.exit()
        else:
            text = "ERROR: Invalid Command. Please choose the correct command.".format(sock.getsockname())
            data = text.encode('ASCII')
            sock.sendto(data, address)
    




def main():
    #Initializing Command Line Arguments
    try:
        parser = argparse.ArgumentParser(description='UDP Server')
        parser.add_argument('portNumber', metavar='PORT NUMBER', type=int, help='UDP Port Number greater than 5000')
        args = parser.parse_args()

        if args.portNumber < 5000 or args.portNumber > 65535:
            print("\nERROR: Invalid Port Number. Please enter Port Number in between 5000 and 65535")
            print("\nProgram Terminated")
            sys.exit()
        print('='*50)
        print("UDP File Server: ")
        print('='*50)

        serverListen(args.portNumber)
    
        
    except ConnectionResetError as e:
        print(e)
        print("\nServer Down! Try again.")
        main()
    except KeyboardInterrupt:
        print("\nProgram Terminated")    
    finally:
        sock.close()
        sys.exit()
if __name__ == '__main__' : main()