#!/usr/bin/env python

#Author: Lakshay Karani lakshay.karani@colorado.edu
#Server Contents: HTTPServer.py,  HTTPClient.py, ws.conf, document root directory
#purpose: To Create a HTTP Based Web Server that handles multiple simultaneous requests from users.    
#Python version: 3.5.1

import socket, sys, os, re, gzip
import threading, hashlib, time
from bs4 import BeautifulSoup


#Module to extract Proxy Port Number and Maximum Cache Time from the Command line
def extractPort(argument):
    #Checks for the number of arguments as 3
    if len(argument) != 3:
        print("Invalid Command. Enter command as: webproxy.py [PortNumber]& MaxCacheTime\nNote: Port Number should be in between 5000 and 65535.\nEnter MaxCacheTime in seconds")
        sys.exit()
        
    #Checks for a Valid Integer
    try:
        portNumber = int(argument[1].rstrip("&"))
        maxCacheTime = int(argument[2])
    except ValueError:
        print("Not a valid Integer. Please enter an int value")
        sys.exit()
    except KeyboardInterrupt as e:
        print(e)
        print("PortNumber should be an Integer.")
        sys.exit()
    
    #Checks for a Valid integer in between 5000 to 65535
    if portNumber not in range(5000,65536):
        print("Invalid PortNumber. Port Number should be in between 5000 and 65535.")
        sys.exit()
    
    return portNumber, maxCacheTime
    

#Module to extract URL information from Requested URL
def urlParser(requestURL):
    #print("URL Parser",requestURL)
    requestURLtemp = requestURL.replace('http://', '').replace('https://', '')
    requestURLPath = '/'
    requestURLServer = None
    requestURLPort = None
    if '/' in requestURLtemp:
        requestURLList = requestURLtemp.split("/", 1)
        requestURLPath = requestURLList[1]
        if ':' in requestURLList[0]:
            requestURLServer = requestURLList[0].split(':')[0]
            requestURLPort = requestURLList[0].split(':')[1]
        else:
            requestURLServer = requestURLList[0]
            requestURLPort = 80
    elif ':' in requestURLtemp:
        requestURLServer = requestURLtemp.split(':')[0]
        requestURLPort = requestURLtemp.split(':')[1]
    else:
        requestURLServer = requestURLtemp
        requestURLPort = 80                    
    return requestURLServer, int(requestURLPort), requestURLPath

#Starting Proxy Connection and listening for requests.     
def proxyConnection(portNumber, maxCacheTime):
    

    try:
        if not os.path.exists("cache"):
            os.makedirs("cache")            

        proxySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxySocket.bind(('', portNumber))
        proxySocket.listen()
        print("Proxy Server Started Successfully.")

        while True:
            
            print("Listening at {}...".format(proxySocket.getsockname()))
            proxyConn, proxyAddr = proxySocket.accept()
            proxyThread = threading.Thread(target = proxySend, args = (proxyConn, proxyAddr, maxCacheTime,))   
            proxyThread.start()
            
    except KeyboardInterrupt as e:
        print(e)
        proxyConn.close()
        sys.exit()
    except Exception as e:
        print(e)
        return

#Accepting requests from client
def proxySend(proxyConn, proxyAddr, maxCacheTime):
    
    
    try:
        recvdData = []
        proxyConn.settimeout(10)

        while True:
            try:
                rawData = proxyConn.recv(4096)
                recvdData.append(rawData)
                if rawData == b'' or rawData.endswith(b'\r\n\r\n') : break
            
            except socket.timeout as e:
                print(e)
                break
            
        requestedData = b''.join(recvdData)

        if not requestedData : return
        #rawData = requestedData.decode('ASCII')
        connectionKeepAlive = False
        if b'keep-alive' in requestedData:
            connectionKeepAlive = True
        
        #Extract Header information from HTTP Request    
        httpRequest = requestedData.splitlines()
        requestMethod,requestURL, requestVersion = httpRequest[0].split()

            
        errorCheck(requestMethod.decode(),requestURL.decode(), requestVersion.decode(), proxyConn)

        requestURLServer,requestURLPort,requestURLPath = urlParser(requestURL.decode())

            
        print("Thread {} : Serving request {}".format(threading.currentThread().getName(), requestURL))
        #Creating a HASH of requested URL and checking the URL for cached data    
        hashURL = hashlib.md5()
        hashURL.update(requestURL)
        cacheFile = "cache/" + hashURL.hexdigest()
        hashURL = None
        print("Thread {} : Checking Cache for {}".format(threading.currentThread().getName(), requestURL))
        
        if os.path.isfile(cacheFile):
            print("Thread {} : Cache Found for {}".format(threading.currentThread().getName(), requestURL))

            #Checking Cached Data with Max Cache Time
            if (time.time() - os.path.getctime(cacheFile)) < maxCacheTime:
                with open(cacheFile, 'rb') as cachedFile:
                    #Sending Cached Data to Client
                    proxyConn.sendall(cachedFile.read())
                    print("Thread {}: Sending cached URL to client: {}".format(threading.currentThread().getName(), requestURL))
            else:
                #Deleting Cached Data
                print("Thread {}: Deleting Cached URL: {} Last modified time greater than max time".format(threading.currentThread().getName(), requestURL))
                os.remove(cacheFile)
                
                #Sending HTTP Request to the server
                serverConnection(requestURLServer, requestURLPort, requestURL, requestedData, proxyConn, proxyAddr, connectionKeepAlive)  
    
        else:
            print("Thread {} : Cache Not Found for {}".format(threading.currentThread().getName(), requestURL))
            #Sending HTTP Request to the server
            serverConnection(requestURLServer, requestURLPort, requestURL, requestedData, proxyConn, proxyAddr, connectionKeepAlive)  
        
        return
    
    except socket.timeout as e:
        print(e)
        return
    except socket.gaierror as e:
        print("Address not found: ", e)
        return

    except KeyboardInterrupt as e:
        print(e)
        sys.exit()
    except Exception as e:
        print(e)
        return

def serverConnection(requestURLServer, requestURLPort, requestURL, requestedData, proxyConn, proxyAddr, connectionKeepAlive):
    try:
        #print("{} {} {}".format(requestURLServer, requestURLPort, requestURLPath))
        #Connecting and Sending the HTTP Request to the Server
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #print((requestURLServer,requestURLPort))
        serverSocket.connect((requestURLServer,requestURLPort))
        print("Thread {}: Creating a Socket Connection and Sending Client request to {} ".format(threading.currentThread().getName(), requestURL))
        serverSocket.send(requestedData)
        serverSocket.settimeout(10)
        #Receiving HTTP Response from the Server
        serverThread = threading.Thread(target = proxyRecv, args = (proxyConn, proxyAddr, serverSocket, requestURL, requestURLServer,requestURLPort, connectionKeepAlive, ))    
        serverThread.start()
        #proxyRecv(proxyConn, proxyAddr, serverSocket, requestURL, requestURLServer, requestURLPort, connectionKeepAlive)
    

    except KeyboardInterrupt as e:
        print(e)
        serverSocket.close()
        proxyConn.close()
        sys.exit()
    except socket.gaierror as e:
        print("Address not found: ", e)
        return
    except Exception as e:
        print(e)
        return

def proxyRecv(proxyConn, proxyAddr, serverSocket, requestURL, requestURLServer,requestURLPort, connectionKeepAlive):
    

    try:
        print("Thread {}: Receiving data from {} ".format(threading.currentThread().getName(), requestURL))
        #Generating Hash of the URL
        hashURL = hashlib.md5()
        hashURL.update(requestURL)
        cacheFile = "cache/" + hashURL.hexdigest()
        hashURL = None
        linkArray = []
        recvdData = []
        serverSocket.settimeout(10)
        
        #Accepting HTTP Response
        while True:
            try:
                rawData = serverSocket.recv(65535)
                #print(rawData)
                recvdData.append(rawData)
                if rawData == b'' or not connectionKeepAlive : break #'''or rawData.endswith(b'\r\n\r\n')'''
            except socket.timeout as e:
                print(e)
                break
        serverData = b''.join(recvdData)

        if serverData == b'': return
        #Check for Caching Information in HTTP Response
        if b'no-cache' in serverData:
            print("Thread {}: Not caching data: Found no-cache Response for {} ".format(threading.currentThread().getName(), requestURL))
            
        elif b'Not Found' in serverData:
            
            print("Thread {}: Not caching data: File Not Found for {} ".format(threading.currentThread().getName(), requestURL))
                
        else:
            #Caching Data for the Requested URL    
            print("Thread {}: Caching data for {}".format(threading.currentThread().getName(), requestURL))
            with open(cacheFile, 'ab') as fh:
                fh.write(serverData)
                fh.close()
        #Sending Data to Client
        print("Thread {} Sending data for {} ".format(threading.currentThread().getName(), requestURL))
        
        proxyConn.sendall(serverData)
        
        serverSocket.close()
        #LINK PREFETCHING
        if b'Content-Type: text/html' in serverData:
            gzipEncoded = False
            #Extracting HTML Content from HTTP Response
            NewLinePosition = serverData.find(b'\r\n\r\n')
            
            #Check for gzip encoding in HTTP Response header
            if b'Content-Encoding: gzip' in serverData:
                #Decompress Gzip Data into Plain text
                print("Thread {}: Found Gzip Encoding for {} ".format(threading.currentThread().getName(), requestURL))
                decompressedContentData = gzip.decompress(serverData[NewLinePosition+4:])
                soup = BeautifulSoup(decompressedContentData, "html.parser")
            else:
                contentData = serverData[NewLinePosition+4:]
                soup = BeautifulSoup(contentData, "html.parser")                    
            
            count = 0
            
            #Find all the links using Beautiful Soup and store in List
            for link in soup.find_all('a', href = True):
                #print("link",link.get('href'))
                if not link.get('href'): continue
                
                if (link.get('href')).startswith('http'):
                    
                    prefetchURLServer,prefechURLPort,prefetchURLPath = urlParser(link.get('href'))
                    
                    linkArray.append((prefetchURLServer,prefechURLPort,prefetchURLPath))
        
                else:
                    linkArray.append((requestURLServer, requestURLPort, link.get('href')))
                
                count+=1
                #Can prefetch upto 50 links 
                if count >= 50: break
                    
            #Create a Thread for every Prefetched Link for the Requested URL
            for link in linkArray:
                prefetchURLServer,prefechURLPort,prefetchURLPath = link
                print("Thread {}: Prefetching links for {} ".format(threading.currentThread().getName(), link))
                
                if not link: continue
                prefetchThread = threading.Thread(target = preFetch, args = (prefetchURLServer,prefechURLPort,prefetchURLPath, ))    
                prefetchThread.start()
        else:
            print("Thread {}: Content-Type is not text/html. Not prefetching data".format(threading.currentThread().getName()))
        
        serverSocket.close()
        return  
    except socket.timeout as e: 
        print(e)
        return
    
    except Exception as e:
        print(e)
        return
    
    except KeyboardInterrupt as e:
        print(e)
        proxyConn.close()
        serverSocket.close()
        sys.exit()

def preFetch(prefetchURLServer,prefechURLPort,prefetchURLPath):  
    
    #Creating a Socket for every PREFETCHED Link
    try:
        prefetchSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #print("PREFETCH: Connecting.. ", prefetchURLServer,prefechURLPort)
        prefetchSocket.connect((prefetchURLServer,prefechURLPort))
        #Connecting and sending a HTTP Request
        preFetchLink =  "http://" + prefetchURLServer.replace("/",'') + "/" + prefetchURLPath.lstrip('/')
        
        httpRequest = b'GET ' + preFetchLink.encode() + b' HTTP/1.1\r\nHost: ' + prefetchURLServer.encode() + b' Connection: close'+ b'\r\n\r\n'
        prefetchSocket.send(httpRequest)
        recvdData = []
        
        prefetchSocket.settimeout(20)
        #Receving and Storing the Prefetched data in Cache
        while True:
            try:
                rawData = prefetchSocket.recv(65535)
                recvdData.append(rawData)
            
                if not rawData  : break #'''or rawData.endswith(b'\r\n\r\n')'''
            except socket.timeout as e:
                print(e)
                break
        
        preFetchedData = b''.join(recvdData)
        if not preFetchedData: return
        
        #PREFETCHING data and Storing in Cache
        hashURL = hashlib.md5()
        hashURL.update(preFetchLink.encode())
        cacheFile = "cache/" + hashURL.hexdigest()
        #print("Pretching data")
        with open("cache/index.txt", 'a') as index:
            index.write(preFetchLink + "        " + hashURL.hexdigest() + "\n")
            index.close
        #Creating an index for HASH name and URL Prefetched    
        with open(cacheFile, 'ab') as fh:
            fh.write(preFetchedData)
            #print("PREFETCHED",preFetchLink, cacheFile)
            fh.close()
        hashURL=None
        prefetchSocket.close()
        print("Thread {}: Prefetch Complete for {} ".format(threading.currentThread().getName(), preFetchLink))
        return
        

    except TimeoutError as e:
        print(e)
        return
    except socket.gaierror as e:
        print("Address not found: ", e)
        return
    except KeyboardInterrupt as e:
        print(e)
        prefetchSocket.close()
        sys.exit()
      
    
def errorCheck(requestMethod,requestURL, requestVersion, proxyConn):
    
    HTTPMethods = ["HEAD" ,"GET", "POST", "OPTIONS", "PUT", "DELETE", "TRACE", "CONNECT"]

    success = True    
    #ERROR CHECK FOR INVALID METHOD
    if requestMethod not in HTTPMethods:
        success = False
        print("Invalid Method {}".format(requestMethod))
        errMsg = "\n\n<html><body><h1>400 BAD REQUEST REASON. INVALID METHOD "+requestMethod+" </h1></body></html>\n\n"
        sendError(" 400 Bad Request", errMsg, proxyConn)
        return success
    #ERROR CHECK FOR INVALID VERSION
    if requestVersion not in  ("HTTP/1.0", "HTTP/1.1"):
        success = False
        print("Invalid requestVersion {}".format(requestVersion))
        errMsg = "\n\n<html><body><h1>400 BAD REQUEST REASON. INVALID VERSION "+requestVersion+" </h1></body></html>\n\n"
        sendError(" 400 Bad Request", errMsg, proxyConn)
        return success
    
    #ERROR CHECK FOR INVALID VERSION        
    if '/' not in requestURL:
        success = False
        print("Invalid requestURL {}".format(requestURL))
        errMsg = "\n\n<html><body><h1>400 BAD REQUEST REASON. INVALID URL "+requestURL+" </h1></body></html>\n\n"
        sendError(" 400 Bad Request", errMsg, proxyConn)
        return success

    #ERROR CHECK FOR METHOD NOT SUPPORTED    
    if requestMethod not in ("GET"):
        success = False
        print("Method {} not Implemented".format(requestMethod))
        errMsg = "\n\n<html><body><h1>501 Not Implemented. Request Method Not Supported: "+requestMethod+" </h1></body></html>\n\n"
        sendError(" 501 Not Implemented", errMsg, proxyConn)
        return success
    
    #ERROR CHECK FOR VERSION NOT SUPPORTED
    if requestVersion not in ("HTTP/1.0"):
        success = False
        print("requestVersion {} not Implemented".format(requestVersion))
        errMsg = "\n\n<html><body><h1>501 Not Implemented. Request Version Not Supported: "+requestVersion+" </h1></body></html>\n\n"
        sendError(" 501 Not Implemented", errMsg, proxyConn)
        return success
    
    return success

def sendError(errorCode, errMsg, proxyConn): #Sending HTTP ERROR RESPONSES
        http_header = "HTTP/1.0" + errorCode
        http_response = http_header + errMsg
        print("Sending Error")
        proxyConn.sendall(http_response.encode('ASCII'))
        
    
def main():
    portNumber, maxCacheTime = extractPort(sys.argv)
    #proxyConnection
    proxyConnection(portNumber, maxCacheTime)      
    
if __name__ == "__main__": main()
