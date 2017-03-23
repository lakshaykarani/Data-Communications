#!/usr/bin/env python

#Author: Lakshay Karani lakshay.karani@colorado.edu
#Server Contents: HTTPServer.py,  HTTPClient.py, ws.conf, document root directory
#purpose: To Create a HTTP Based Web Server that handles multiple simultaneous requests from users.    
#Python version: 3.5.1
import socket, sys, os, re, threading
from re import IGNORECASE
from datetime import datetime

def sendError(errorCode, errMsg, client_connection, requestVersion = "HTTP/1.0"): #Sending HTTP ERROR RESPONSES
        http_header = requestVersion + errorCode
        http_response = http_header + errMsg
        client_connection.sendall(http_response.encode('ASCII'))
        return

class ClientThread(threading.Thread):
    def __init__(self, client_connection, address, conf, sock):
        threading.Thread.__init__(self)
        self.client_connection = client_connection
        self.address = address
        self.conf = conf
        self.sock = sock

     
    def run(self):
        try:
            startTime = datetime.now()
            print("{} Start Time {}".format(threading.currentThread().getName(), startTime))
            
            #print("{} started\n".format(threading.currentThread().getName()))
            KeepAliveflag = True
            while KeepAliveflag: #If Connection: keep-alive
                 
                try:
                    rawRequest = self.client_connection.recv(1024)
                except socket.timeout as e: #Check for Timeout Value
                    print("{}: Connection Timed Out".format(threading.currentThread().getName()))
                    break
                except ConnectionResetError as e:
                    break
                request = rawRequest.decode('ASCII')
    
                requestLine = request.split('\n')
                
                if requestLine != ['']:    
                    requestMethod,requestURL, requestVersion = requestLine[0].split() #Extract requestMethod,requestURL, requestVersion
                    for line in requestLine:
                        if re.search("keep-alive", line, IGNORECASE): #Check for Keep Alive
                            KeepAliveflag = True
                            self.client_connection.settimeout(int(self.conf['KeepaliveTime']))
                            break
                        else:
                            KeepAliveflag = False
                            
                            
                    requestImplemented = ['GET', 'HTTP/1.0', 'HTTP/1.1']
                    
                    requestNotImplemented = ['OPTIONS','PUT', 'DELETE', 'TRACE','CONNECT','HEAD', 'POST']
                    #Check for Error in Request, if yes, Send and error response    
                    if not re.search("/", requestURL):
                        errMsg = "\n\n<html><body><h1>400 BAD REQUEST REASON. INVALID METHOD "+requestMethod+" </h1></body></html>\n\n"
                        sendError(" 400 Bad Request", errMsg, self.client_connection)
                        break
        
                    if not (requestMethod in requestImplemented) and not (requestMethod in requestNotImplemented):
                        errMsg = "\n\n<html><body><h1>400 BAD REQUEST REASON. INVALID METHOD "+requestMethod+" </h1></body></html>\n\n"
                        sendError(" 400 Bad Request", errMsg, self.client_connection)
                        break
        
                    
                    if not (requestVersion in requestImplemented):
                        errMsg = "\n\n<html><body><h1>400 BAD REQUEST REASON. INVALID VERSION "+requestVersion+" </h1></body></html>\n\n"
                        sendError(" 400 Bad Request", errMsg, self.client_connection)
                        break
                    
                    if requestMethod in requestNotImplemented:
                        errMsg = "\n\n<html><body><h1>501 Not Implemented. Request Method Not Supported: "+requestMethod+" </h1></body></html>\n\n"
                        sendError(" 501 Not Implemented", errMsg, self.client_connection)
                        break  
                        
       
                    if requestURL == "/": #Check for index page
                        index = self.conf['DirectoryIndex'].split(" ")  #DirectoryIndex index.html index.htm index.ws customdefaultfile.htm
                        for file in index:
                            filePath = self.conf['DocumentRoot'].strip() + '\\' + file
                            if os.path.isfile(filePath):
                                errFlag = False
                                with open(filePath, 'rb') as fh:
                                    http_response = fh.read()
                                    self.client_connection.sendall(http_response)     #Send index page
                            else:
                                errFlag = True
                        if errFlag:
                            errMsg = "\n\n<html><body><h1>404 Not Found: Index page not Found "+requestURL+" </h1></body></html>\n\n"
                            sendError(" 404 Not Found", errMsg, self.client_connection, requestVersion)
                    else:
                        filePath = self.conf['DocumentRoot'].strip() + requestURL
                        file_name, fileExtension = os.path.splitext(requestURL)
                       
                        if os.path.isfile(filePath):   #Check for requested URL
                            if not (fileExtension in self.conf['ContentType']):#Check if extention not present in ws.conf
                                errMsg = "\n\n<html><body><h1>501 Not Implemented. File Type Not Supported: "+requestURL+" </h1></body></html>\n\n"
                                sendError(" 501 Not Implemented", errMsg, self.client_connection)
                                break  

                            with open(filePath, 'rb') as fh:
                                requestedFile = fh.read()
                                http_header = requestVersion + " 200 OK" + "\nContent-Type: " + self.conf['ContentType'][fileExtension] + "\nContent-Length: " + str(len(requestedFile)) 
                                if requestVersion == "HTTP/1.1":
                                    if KeepAliveflag:
                                        http_header = http_header + "\nConnection: keep-alive" + "\n\n"
                                    else:
                                        http_header = http_header + "\nConnection: close" + "\n\n"
                                else:
                                    http_header = http_header + "\n\n"
                                http_response = http_header.encode() + requestedFile
                                self.client_connection.sendall(http_response)           #Send Requested File to the Client
                        
                        else:
                            errMsg = "\n\n<html><body><h1>404 Not Found: Reason URL does not exist: "+requestURL+" </h1></body></html>\n\n"
                            sendError(" 404 Not Found", errMsg, self.client_connection, requestVersion)
                                
                else:
    
                    print("{}: Blank Request: Closing Connection. ".format(threading.currentThread().getName()))
                    break
                
            self.client_connection.shutdown(socket.SHUT_RDWR)
            self.client_connection.close()
            endTime = datetime.now()
            print("{} End Time {}".format(threading.currentThread().getName(), endTime ))
            print("{} Time Difference: {}".format(threading.currentThread().getName(), endTime - startTime))
            return
        
        except KeyError as e:
            print(e) #If something wrong with Server Configuration File, Send an Error
            notFoundError = "\n\n<html><body><h3>500 Internal Server Error: Cannot Allocate Memory. Check the Server Configuration File.\nCannot find "+str(e)+" in ws.conf </h3></body></html>\n\n"
            sendError(" 500 Internal Server Error", errMsg, self.client_connection)
            

                
        

def readConf(confFile):
    #Reading ws.conf File and Creating a Dictionary conf.
    conf = {}
    content = {}
    if os.path.isfile(confFile):
        with open(confFile) as fh:
            for line in fh.readlines():
                if line != "":  
                    if not re.match('#', line):
                        if re.search('ContentType', line):
                            contentLine = line.split()
                            content[contentLine[1]] = contentLine[2]
                            conf['ContentType'] = content
                        elif re.search('DirectoryIndex', line):
                            text = line.split(" ", 1)
                            conf[text[0]] = line.strip('DirectoryIndex')
                            
                        elif len(line.split(" ", 1)) == 2:                            
                            text = line.split(" ", 1)
                            conf[text[0]] = text[1]
                        
                        else:
                            print("Could not Parse ws.conf")
                            sys.exit()
    else:
        print("ws.conf File Not Found!")
        sys.exit()
        
    return conf

    
def main():
    try:
        conf = readConf('ws.conf')   #Reading ws.conf file
        if int(conf['ListenPort']) < 1024 or int(conf['ListenPort']) > 65535:
            print("Invalid Port Number./n Please Enter the port number in between 1024 and 65535") #Check for valid port numbers
            sys.exit()
            
        host, port = '',int(conf['ListenPort'])
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host,port))
        while True:
            sock.listen()
            print("HTTP Server Listening at {} ...".format(sock.getsockname()))
            client_connection, address = sock.accept() #Accept HTTP requests from client
            newThread = ClientThread(client_connection, address, conf, sock)
            newThread.start() #Start a new Thread
            #print("Active Threads: {}".format(threading.activeCount()))
    except KeyboardInterrupt:
        print("Closing all connections..")  
        sock.close()
        print("Server Shut Down!")
        sys.exit()
            

if __name__ == "__main__":main()