from simplecrypt import encrypt
from simplecrypt import decrypt
import os, sys, collections, socket
import threading, hashlib, time

#End OF File Variable
eof = b'|#|EOF'
#This module is used to read and extract the Server Informations and Username Password from the configuration file DFC.conf 
def readConfiguration(argument):
    
    #Checks for the number of arguments as 2
    if len(argument) != 2:
        print("Invalid Command. Enter command as: dfc.py dfc.conf\nNote: dfc.conf is the configuration file for the DFS Servers")
        sys.exit()
    
    configFile = argument[1]
    print("Reading Configuration file {}".format(configFile))
    serverConfig = {}
    serverCount = 0
    usernameFlag = False
    passwordFlag = False
    
    #Checks for config file if present
    if os.path.isfile(configFile):
        with open(configFile, 'r') as fh:
            for line in fh.readlines():
                if line.upper().startswith("SERVER"):
                    serverName, serverAddress = line.split()[1:3]
                    serverIP, serverPort = serverAddress.split(':')
                    serverConfig[serverName] = (serverIP, int(serverPort)) #Creates a Dictionary for Server Information 
                    serverCount += 1
                
                if line.upper().startswith("USERNAME"):
                    username = line.split()[1]
                    usernameFlag = True
                if line.upper().startswith("PASSWORD"):
                    password = line.split()[1]
                    passwordFlag = True
                
            if not usernameFlag and not passwordFlag:
                print("Please specify a Username and Password in Dfc.conf")
                sys.exit()
                
            if serverCount!=4:
                print("Something wrong in Conf file.")
                sys.exit()
    else:
        print("dfc.conf Not Found. Please enter a valid configuration file")
        print("Terminating Program")
        sys.exit()
    
    return username, password, serverConfig 


#Main menu for the client to perform an operation
def acceptOperation():
    
    
    prompt = "> "
    #os.system('cls')
    
    print('='*50)
    print("Distributed File Storage: ")
    print('='*50)
    print("Choose an operation:")
    print("o GET [file_name] [sub_folder]")
    print("o PUT [file_name] [sub_folder]")
    print("o LIST [sub_folder]")
    print("o MKDIR [sub_folder]")
    
    try:
        argument = input(prompt).split(" ", 2)
    except ValueError:
        print("Error while passing values")
        pass
    except EOFError:
        print("Terminating Program")
        sys.exit()
    
    statusOk = True
    filename = ''
    requestedOperation = ''
    subfolder = ''
    
    if len(argument) == 3:
        requestedOperation = argument[0]
        filename = argument[1]
        subfolder = argument[2]
        
    elif len(argument) == 2:
        requestedOperation = argument[0]
        if requestedOperation == "LIST":
            subfolder = argument[1]
        else:    
            filename = argument[1]
        
    elif len(argument) == 1:
        requestedOperation = argument[0]
    else:
        print("Please Enter a Valid Command: [GET [file_name], PUT [file_name], LIST")


    if requestedOperation.upper() not in ["GET", "PUT", "LIST", "MKDIR"]:
        print("Please Enter a Valid Command: [GET [file_name] [sub_folder], PUT [file_name] [sub_folder], LIST [sub_folder], MKDIR  [sub_folder]")
        statusOk = False
    
    if requestedOperation.upper() in ["GET", "PUT", "MKDIR"] and filename == '':
        print("Please Enter a Valid Command: [GET [file_name], PUT [file_name], LIST, MKDIR [Folder_Name]")
        statusOk = False
    
    return requestedOperation.upper(), filename, statusOk, subfolder.strip()

def recvAll(sock, maxBytes = 2048):
    
    temp = []   
    sock.settimeout(20)
    while True:
        try:
            rawData = sock.recv(maxBytes)
            temp.append(rawData)
            if rawData.endswith(b'|#|EOF'): break
        except socket.timeout as e:
            print(e)
            break
    recvdData = b''.join(temp)
    
    return recvdData


#This Module authenticates a user based on the username password info in dfc.conf file
def authenticate(serverAddress, serverName, username, password, firstTime):
    try:
        accessGranted = False
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(serverAddress)
        #Sends Request with Header Information
        rawData = b'AuthenticateUser|#|' + username.encode() + b'|#|' + password.encode() + eof
        sock.sendall(rawData)
        recvdData = recvAll(sock,2048)
        sock.close()
        if recvdData == b'': 
            print("RecvAll Error")
            raise ConnectionRefusedError
                    
        temp = recvdData.split(b'|#|')
        status = temp[1].decode()
        if firstTime:
            print("Reply from server {}: {}".format(serverName, status))
        serverStatus = True

        if recvdData.startswith(b'AccessGranted'):
            accessGranted = True

        if recvdData.startswith(b'AccessDenied'):
            accessGranted = False
            
    except ConnectionRefusedError as e:
        serverStatus = False
        print("No reply from server {}: {}".format(serverName, e))
        
    finally:        
        return serverStatus , accessGranted

def authenticateUser(username, password, serverConfig, firstTime = True):
    
    serverStatus = {}
    accessGranted = []
    print("\n")
    #Sends request to all authenticate the user on all the 4 servers
    for server in serverConfig.keys():
        status , access = authenticate(serverConfig[server], server, username, password, firstTime )
        serverStatus[server] = status
        accessGranted.append(access)
    
    if accessGranted.count(False) > 2: 
        print("Most of the servers are down. Terminating Program")
        sys.exit()
    print("\n")
    return serverStatus

#Module for fetching the file from the servers as requested by the client
def getFile(filename, subfolder, username, password, serverConfig, serverStatus):
    
    recvdChunks = []
    print("Fetching file from the server...")
    serverUpCount = 0
    serverFilePath = os.path.join(subfolder.strip('/'), filename)
    
    #Fetch File if DFS1 and DFS3 are active
    if serverStatus[sorted(serverStatus)[0]] and serverStatus[sorted(serverStatus)[2]]:

        chunk = recvChunks(serverConfig[sorted(serverStatus)[0]], sorted(serverStatus)[0] , serverFilePath, username)
        recvdChunks.append(chunk)
        chunk = recvChunks(serverConfig[sorted(serverStatus)[2]], sorted(serverStatus)[2] , serverFilePath,username)
        recvdChunks.append(chunk)
        
    #Otherwise Fetch File if DFS2 and DFS4 are active
    elif serverStatus[sorted(serverStatus)[1]] and serverStatus[sorted(serverStatus)[3]]:
        print("DFS 2 and 4")
        chunk = recvChunks(serverConfig[sorted(serverStatus)[1]], sorted(serverStatus)[1] , serverFilePath,username)
        recvdChunks.append(chunk)
        chunk = recvChunks(serverConfig[sorted(serverStatus)[3  ]], sorted(serverStatus)[3] , serverFilePath,username)
        recvdChunks.append(chunk)
    
    else:
        #File cannot be regenerated if more than 2 servers are down
        for server in sorted(serverStatus):
            print("{} Server Status : {}".format(server, 'online' if serverStatus[server] else 'offline'))
        
        if serverStatus[server]: serverUpCount +=1
        
        if serverUpCount < 3: 
            print("Server Down: Your requested data cannot be recovered")
    
    if b'ServerShutDown' in recvdChunks: return
    
    recoverData(recvdChunks, filename, password) 

#Sends GET request to all the servers
def recvChunks(serverAddress, serverName, serverFilePath,username):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(serverAddress)
        userFilePath = serverFilePath
        sendRequest = b'GET|#|' + userFilePath.encode()+ b'|#|'+username.encode()+ eof
        sock.sendall(sendRequest)
        recvdData = recvAll(sock,2048)
        sock.close()
    except ConnectionRefusedError:
        print("Server {} has been unexpectedly shut down. Trying to re-authenticate the server. Please try again".format(serverName))
        recvdData = b'ServerShutDown'
    finally:
        return recvdData


#Process the received data and combine the file pieces are write in a single file
def recoverData(recvdChunks, filename, password):
    rawDataDict = {}
    fileFound = False
    for rx in recvdChunks:
        if rx.startswith(b'FileFound'):
            fileFound = True
        else:
            temp = rx.split(b'|#|')
            serverStatus, serverName = temp[2:4]
            fileFound = False
            print("Reply from Server {}: {}".format(serverName.decode(), serverStatus.decode()))

    if fileFound:
        for chunk in recvdChunks:
            temp = chunk.split(b'|#|')
            rawData, serverStatus, serverName = temp[1:4]

            print("Reply from Server {}: {}".format(serverName.decode(), serverStatus.decode()))
            
            dataChunkGroup = rawData.split(b'|concatChunk|')
            
            chunkHeader, rawDataChunk = dataChunkGroup[0].split(b'|chunk|')
            
            print("Decrypting Data... Please wait...")
            print("This may take a few moments...")

            decryptedChunk = decrypt(password, rawDataChunk)            
            rawDataDict[chunkHeader] = decryptedChunk
            
            chunkHeader, rawDataChunk = dataChunkGroup[1].split(b'|chunk|')
            decryptedChunk = decrypt(password, rawDataChunk)                      
            rawDataDict[chunkHeader] = decryptedChunk
        
        tempDataList = []    
        for chunkData in sorted(rawDataDict):    
            tempDataList.append(rawDataDict[chunkData])
        
        recoverdData = b''.join(tempDataList)
        folderPath, file = os.path.split(filename)
        
        if folderPath == '':
            filePath =  os.path.join("DFC","ReceivedFiles")
        else:
            filePath = os.path.join("DFC","ReceivedFiles" ,folderPath)
        
        if not os.path.exists(filePath):
            os.makedirs(filePath)
            
        print("Your requested file is available at {}".format(filePath))
        with open(os.path.join(filePath ,file), 'wb') as fh:
            fh.write(recoverdData)
            fh.close()        
        

#The requested file is split into 4 chunks which is then encrypted and grouped into pairs.
def splitFile(rawData, password):
    fileSize = len(rawData)
    statusOk = True
    if fileSize == 0:
        print("File size is 0. Cannot send empty file.")
        statusOk = False
    chunkSize, remainder = divmod(fileSize, 4)            
    rawDataChunks = []

    print("Encrypting Data... Please wait...")
    print("This may take a few moments...")
    
    for x in range(0, 4):
        chunkHeader = '{}|chunk|'.format(x+1) 
        if x == 3:

            tempChunk = rawData[x*chunkSize:]
            
            encryptedChunk = encrypt(password, tempChunk)
            rawDataChunks.append(chunkHeader.encode() + encryptedChunk)
        else:
            
            tempChunk = rawData[x*chunkSize:(x+1)*chunkSize]           
            encryptedChunk = encrypt(password, tempChunk)
            rawDataChunks.append(chunkHeader.encode() + encryptedChunk)

    dataChunkGroups = []
    for x in range(0,4):
        if x == 3:
            dataChunkGroups.append((rawDataChunks[x],rawDataChunks[x-x]))
        else:
            dataChunkGroups.append((rawDataChunks[x],rawDataChunks[x+1]))
    
    return rawDataChunks, dataChunkGroups, statusOk

#The PUT Command is used to store file chunks onto the servers in pairs
def putFile(filename, subfolder, username, password, serverConfig):
    filePath = "DFC/"+filename
    serverFilePath = os.path.join(subfolder.lstrip('/'),filename)
    print(serverFilePath)
    if os.path.isfile(filePath):
        with open(filePath, 'rb') as fh:
            rawData = fh.read()
            rawDataChunks, dataChunkGroups, statusOk = splitFile(rawData, password)   
        if not statusOk : return
        hashFile = hashlib.md5()
        hashFile.update(rawData)
        hexValue = hashFile.hexdigest()
        #Calculate the hash and determine the destination of the file chunks
        index =  int(hexValue, 16) % 4
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #index DFS1  DFS2  DFS3   DFS4
        #0   (1,2) (2,3) (3,4)  (4,1)
        #1   (4,1) (1,2) (2,3)  (3,4)
        #2   (3,4) (4,1) (1,2)  (2,3)
        #3   (2,3) (3,4) (4,1)  (1,2)
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        updatedataChunkGroups = collections.deque(dataChunkGroups)
        
        updatedataChunkGroups.rotate(index)   
        
        DFServers = ["DFS1","DFS2","DFS3","DFS4"]
        chunkDest = {}
        
        for x in range(0,4):
            chunkDest[DFServers[x]] = updatedataChunkGroups[x]
        
        for server in chunkDest.keys():
            serverThread = threading.Thread(target=sendChunks, args=(serverConfig[server], server, chunkDest[server], serverFilePath,username,))
            serverThread.start()
        
    else:
        print("File not found: {}".format(filePath))
        print("Place the file in DFC/ directory")

#This will send all the chunks to respective servers
def sendChunks(serverAddress, serverName, dataChunk, serverFilePath, username):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(serverAddress)
        sendRequest = b'PUT|#|' + serverFilePath.encode()+b'|#|'+ b'|concatChunk|'.join(dataChunk) +b'|#|'+username.encode()+ eof
        sock.sendall(sendRequest)
        print("Sending Data:",threading.current_thread().getName(), serverAddress, serverName)  
        recvdData = recvAll(sock,2048)      
        sock.close()
        if recvdData == b'': 
            print("RecvAll Error")
            sys.exit()
                    
        temp = recvdData.split(b'|#|')
        status = temp[1].decode()
        print("Reply from server {}: {}".format(serverName, status))
        if not recvdData.startswith(b'TransferSuccessful'): acceptOperation()
        return 
    except ConnectionRefusedError as e:
        print("No reply from server {}: {}".format(serverName, e))
        pass


#This module is used to fetch the List of files available for the current user
def fetchList(serverAddress, serverName, username, password, subfolder):

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(serverAddress)
        rawData = b'LIST|#|' + username.encode() + b'|#|' + subfolder.encode() + eof
        sock.sendall(rawData)
        recvdData = recvAll(sock,2048)
        sock.close()
        if recvdData == b'': 
            print("RecvAll Error")
            sys.exit()

        temp = recvdData.split(b'|#|')
        status, fileString = temp[1:3]
        print("Reply from server {}: {}".format(serverName, status.decode()))
        
        if recvdData.startswith(b'FilesFound'):
            listFiles = fileString.split(b'|file|')
            FilesFound = True
        else:
            FilesFound = False
            listFiles = b''
        return listFiles, FilesFound


    except ConnectionRefusedError as e:
        print("No reply from server {}: {}".format(serverName, e))
        listFiles, FilesFound = b'' , False 
        return listFiles, FilesFound
        

#This fetches file list from every server also determines if file can be regenerated
def listFile(subfolder, username, password, serverConfig, serverStatus):
    
    fileListDict = {}
    FileFound = []
    for server in sorted(serverConfig):
        listFiles, FileStatus= fetchList(serverConfig[server], server, username, password, subfolder)
        FileFound.append(FileStatus)
        fileListDict[server] = listFiles
        
    if FileFound.count(True) < 2:return
    
    fileStatus = {}  
    
    if serverStatus['DFS1'] and serverStatus['DFS3']:

        for DFS1File in fileListDict['DFS1']:
            if DFS1File in fileListDict['DFS3']:
                fileStatus[DFS1File] = 'Complete'
            else:
                fileStatus[DFS1File] = 'Incomplete'
    elif serverStatus['DFS2'] and serverStatus['DFS4']:
            
        for DFS2File in fileListDict['DFS2']:
            if DFS2File in fileListDict['DFS4']:
                fileStatus[DFS2File] = 'Complete'
            else:
                fileStatus[DFS2File] = 'Incomplete'
    else:
        serverUpCount = 0
        for server in sorted(serverStatus):
            print("{} Server Status : {}".format(server, 'online' if serverStatus[server] else 'offline'))
        
            if serverStatus[server]: 
                for DFSFile in fileListDict[server]:
                    fileStatus[DFSFile] = 'Incomplete'
                serverUpCount +=1
        
        if serverUpCount < 3: 
            print("Servers Down: Your requested data cannot be recovered")
    
    
    print("="*50)
    print("Files Available for {}".format(username))
    print("="*50)
    for file in fileStatus.keys():
        print("o {} {}".format(file.decode(), fileStatus[file])) 
        

#This module is used to create an empty directory based in MKDIR on all servers
def makedirectory(filename, username, password, serverConfig, serverStatus):
    

    for server in sorted(serverConfig):
        try:

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(serverConfig[server])
            rawData = b'MKDIR|#|' + filename.encode() + b'|#|' +username.encode() + eof
            sock.sendall(rawData)
            recvdData = recvAll(sock,2048)
            sock.close()
        
            if recvdData == b'': 
                print("RecvAll Error")
                sys.exit()

            temp = recvdData.split(b'|#|')
            status = temp[1].decode()
            print("Reply from server {}: {}".format(server, status))
        except ConnectionRefusedError as e:
            print("No reply from server {}: {}".format(server, e))
            pass


             
def main():
    
    try:
        username, password, serverConfig = readConfiguration(sys.argv)
        serverStatus = authenticateUser(username, password, serverConfig)

        while True:
            requestedOperation, filename, statusOk, subfolder = acceptOperation() 
            if statusOk:
                if requestedOperation == "GET":
                    getFile(filename, subfolder, username, password, serverConfig, serverStatus)
                
                if requestedOperation == "PUT":
                    putFile(filename, subfolder, username, password, serverConfig)
                
                if requestedOperation == "LIST":
                    listFile(subfolder, username, password, serverConfig, serverStatus)
            
                if requestedOperation == "MKDIR":
                    makedirectory(filename, username, password, serverConfig, serverStatus)
            #if requestedOperation == "EXIT":
            #    exitProgam()
            serverStatus = authenticateUser(username, password, serverConfig, firstTime=False)            
            
            time.sleep(1)   
    except KeyboardInterrupt:
        print("Terminating Program")
        sys.exit()
if __name__ == '__main__': main()