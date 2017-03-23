import os, re, sys, socket
import threading, hashlib, time

eof = b'|#|EOF'

#This module will read the configuration file stored in the the root folder along with DFS.py
#It will extract all the Username and Password associated with the server

def readConfiguration(argument):
    
    #Checks for the number of arguments provided in command line
    print("Reading Server Configuration File...")
    if len(argument) != 3: 
        print("Invalid Command. Enter command as: dfs.py /DFS[1-4] [PortNumber] &\nNote: dfs.conf is the configuration file for the DFS Servers")
        sys.exit()
    
    serverName = argument[1].lstrip('/')
    configFile = argument[1].lstrip('/') + "/dfs.conf"
    portNumber = argument[2]
    usernamePassword = {}
    
    if os.path.isfile(configFile):
        with open(configFile, 'r') as fh:
            for line in fh.readlines():
                temp = line.split()
                if len(temp) !=2: #Server will shut down if there is something wrong with configuration file
                    print("Something wrong with dfs.conf")
                    sys.exit()
                    
                username, password = temp
                usernamePassword[username] = password
                #print(usernamePassword)

    else:
        print("dfs.conf Not Found. Please enter a valid configuration file")
        print("Terminating Program")
        sys.exit()
    
    return usernamePassword, serverName, int(portNumber)

#This module verifies the incoming username and password and authenticates the client.
def authenticateUser(recvdData, usernamePassword, clientConnection):
    temp = recvdData.split(b'|#|')
    clientUsername, clientPassword = temp[1:3]
    print("Authenticating user {}...".format(clientUsername))
    #It checks the received username and password with the details extracted from DFS.conf file
    if clientUsername.decode() in usernamePassword.keys() and usernamePassword[clientUsername.decode()] == clientPassword.decode():
        status = "Authentication Successful: {}".format(clientUsername)
        sendingData = b'AccessGranted|#|' + status.encode() + eof
    else:
        status = "Client {} : Invalid Username/Password.\nAccess Denied.".format(clientUsername)
        sendingData = b'AccessDenied|#|' + status.encode() + eof
    print(status)
    clientConnection.sendall(sendingData)

#This module is used to process the received files and store the files in respective directories in the server
def getData(recvdData, clientConnection, serverName):
    temp = recvdData.split(b'|#|')
    fileFound = False
    rawDataList = []
    fileName, username = temp[1:3]
    print("Fetching data for {}".format(username.decode()))
    folderPath, file = os.path.split(fileName.decode())

    #This checks if there is a need to create a Sub-Folder to store the file        
    if folderPath == '':
        userPath = os.path.join(serverName ,username.decode()) 
    else:
        userPath = os.path.join(serverName , username.decode(), folderPath )
    
    if os.path.exists(userPath):
        for serverFile in os.listdir(userPath):
            if re.search(file, serverFile):
                fileFound = True
                filePath = userPath +'/'+serverFile
                temp = serverFile.lstrip('.')
                chunkID = temp.replace(file, '')
                with open(filePath, 'rb') as fh:
                    fileChunk = chunkID.encode() + b'|chunk|' + fh.read()
                    fh.close()
                rawDataList.append(fileChunk)    
    
    #This concatinates the requested data chunk to be sent over the network
    rawData = b'|concatChunk|'.join(rawDataList)
    
    if fileFound:
        status = "Transferring Data... \nRequested file {} is {} bytes long".format(fileName, len(rawData))
        sendingData = b'FileFound|#|' + rawData + b'|#|' + status.encode() + b'|#|' + serverName.encode() + eof 
    else:
        status = "File Not Found. File Transfer Failed: {}".format(fileName.decode())
        sendingData = b'FileNotFound|#|' + rawData + b'|#|' + status.encode() + b'|#|' + serverName.encode() + eof
        
    print(status)
    clientConnection.sendall(sendingData)
        

#This module is run when Client requests to store a file on the servers
def putData(recvdData, clientConnection, serverName):
    
    
    temp = recvdData.split(b'|#|')
    fileName, rxDataChunk , username = temp[1:4]
    if rxDataChunk == b'':
        print("ERROR in rxDataChunk")
        return

    print("Storing Data for {}".format(username))
    dataChunkGroup = rxDataChunk.split(b'|concatChunk|')
    
    for chunk in dataChunkGroup:
        chunkHeader, rawDataChunk = chunk.split(b'|chunk|')
        #print(serverName, username, fileName, chunkHeader)
        folderPath, file = os.path.split(fileName.decode())
        if not os.path.exists(os.path.join(serverName, username.decode())):
            os.makedirs(os.path.join(serverName, username.decode()))

        if folderPath != '':
            if not os.path.exists(os.path.join(serverName , username.decode(),folderPath)):
                os.makedirs(os.path.join(serverName , username.decode(),folderPath))

            filePath = os.path.join(serverName,username.decode(), folderPath,'.'+file+'.'+chunkHeader.decode())
        else:
            filePath = os.path.join(serverName,username.decode(),'.'+file+'.'+chunkHeader.decode())
        
        print("filePath",filePath)    
        #This stores the file on the server depending on the chunk received    
        with open(filePath, 'wb') as fh:
            fh.write(rawDataChunk)
            fh.close()

        if os.path.getsize(filePath) > 0:
            status = "File Transfer Successful: {}".format(fileName)
            sendingData = b'TransferSuccessful|#|' + status.encode() + eof
        else:
            status = "File Transfer Failed: {}".format(fileName)
            sendingData = b'TransferFailed|#|' + status.encode() + eof
            
        
    print(status)
    clientConnection.sendall(sendingData)

#This Module is used to list the files available on the server and also whether if it can be successfully regenerated
def listData(recvdData, clientConnection, serverName):
    
    temp = recvdData.split(b'|#|')
    print(temp)
    username, subfolder = temp[1:3]
    print("Sending a List of Files available on the server for {}".format(username.decode()))
    if subfolder != b'':
        userDir = os.path.join(serverName,username.decode(),(subfolder.decode()).lstrip('/'))
    else:
        userDir = os.path.join(serverName,username.decode())
    
    print(userDir)        
    serverFile= []   
    fileString = ''
    listFiles = []
    #Checks all the directories and sub directories and returns a list of files available
    if os.path.exists(userDir):
        for path, subdirs, files in os.walk(userDir):
            for name in files:
                listFiles.append(os.path.join(path, name))
        if listFiles != ['']:
            for rawfile in listFiles:
                folderPath, file = os.path.split(rawfile)
                userPath = os.path.relpath(folderPath, serverName)
                temp = file.lstrip('.')
                fileName = temp[:-2]
                serverFile.append(os.path.join(userPath, fileName))
            fileSet = set(serverFile)

            fileString = '|file|'.join(fileSet)
            
            status = "Sending File List for {}".format(username.decode())
            sendingData = b'FilesFound|#|' + status.encode() + b'|#|' +fileString.encode() + eof
        else:       
            status = "No Files Available for {} ".format(username.decode())
            sendingData = b'NoFiles|#|' + status.encode() +  b'|#|' +fileString.encode() +  eof
                

    else:       
        status = "No Files Available for {} ".format(username.decode())
        sendingData = b'NoFiles|#|' + status.encode() +  b'|#|' +fileString.encode() + eof
 
    print(status)
    clientConnection.sendall(sendingData)
    
#This module is used to create a directory on the server as specified by the client
def makeDirectory(recvdData, clientConnection, serverName):
    
    temp = recvdData.split(b'|#|')
    folderName, username = temp[1:3]
    print("Creating a Directory for {}".format(username.decode()))
    folderPath = serverName + '/' + username.decode() + '/' + folderName.decode() 
    print(folderPath)
    if os.path.exists(folderPath):
        folderExists = True
    else: 
        os.makedirs(folderPath)
        folderExists = False
    
    if folderExists:
        status = "Directory {} already exists in the server.".format(folderName.decode())
        sendingData = b'FolderExists|#|' + status.encode() + eof 
    else:
        status = "Directory {} created.".format(folderName.decode())
        sendingData = b'FolderCreated|#|' + status.encode() + eof

    print(status)
    clientConnection.sendall(sendingData)


#Creates a thread for serving simultaneous connections from clients       
def newClientThread(clientConnection, clientAddress, usernamePassword, serverName):
    
    temp = []  
    print("{}: Incoming Client Connection: {}".format(threading.current_thread().getName(), clientAddress))
    while True:
        try:
            rawData = clientConnection.recv(2048)
            temp.append(rawData)
            if rawData.endswith(b'|#|EOF'): break
        except socket.timeout as e:
            print(e)
            break
    recvdData = b''.join(temp)

        
    if recvdData.startswith(b'AuthenticateUser'):
        authenticateUser(recvdData, usernamePassword, clientConnection)

    
    elif recvdData.startswith(b'GET'):
        getData(recvdData, clientConnection, serverName)        
    elif recvdData.startswith(b'PUT'):
        putData(recvdData, clientConnection, serverName)
    elif recvdData.startswith(b'LIST'):
        listData(recvdData, clientConnection, serverName)
    elif recvdData.startswith(b'MKDIR'):
        makeDirectory(recvdData, clientConnection, serverName)
    else:
        print(b'Invalid request sent')
    
    return
    
    
def main():

    try:
        usernamePassword, serverName, portNumber = readConfiguration(sys.argv)
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind(('', portNumber))
        serverSocket.listen()
        while True:
            print("DFS Server Listening at {} ...".format(serverSocket.getsockname()))
            clientConnection, clientAddress = serverSocket.accept() #Accept HTTP requests from client
            newThread = threading.Thread(target= newClientThread, args = (clientConnection, clientAddress, usernamePassword, serverName,))
            newThread.start() #Start a new Thread
            
    except OSError as e:
        print(e)
        print("Port Number in use. Server already running.")
        sys.exit()
        
    except KeyboardInterrupt:
        print("Server Shut Down")
        sys.exit()
        
if __name__ == "__main__": main()