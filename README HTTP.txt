#Author: Lakshay Karani lakshay.karani@colorado.edu
#Server Contents: HTTPServer.py,  HTTPClient.py, ws.conf, document root directory
#purpose: To Create a HTTP Based Web Server that handles multiple simultaneous requests from users.	
#Python version: 3.5.1

BEFORE RUNNING THE HTTP BASED WEB SERVER:

o There should be a 'document root directory' named 'www' which will contain all the files that could be requested by the user.
o The ws.conf file should be in a directory along with HTTPServer.py, HTTPClient.py and 'www'.
o ws.conf should contain all the necessary configuration parameters
	- ListenPort: Port at which the server will listen to all the requests
	- DocumentRoot: Path to the 'document root directory' i.e. 'www'
	- DirectoryIndex: Look up table for index page if present.
	- ContentType: All the file types that are supported by the Server
	- KeepaliveTime: Timeout value if there is a Connection: keep-alive set by the client.
o Restart the Server if any value is changed.

o Multi-Threaded approach is used to serve multiple requests from Clients.

TO RUN THE SERVER:
o Open the command prompt and run HTTPServer.py
o By default, Server is running on 127.0.0.1:9999.
o Open http://127.0.0.1:9999/ on a Web Browser. You should see and Index page.

o The Web Server is only capable of serving GET Requests as of now.
o It is compatible with HTTP/1.1 and HTTP/1.0
o Pipelining is supported by the browser i.e. if there is a Connection: keep-alive in the request, the thread will remain open for KeepaliveTime as set in ws.conf file.
o Error Codes Supported by the Browser:
	- 400 Bad Request: Reason Invalid Method -> Error if there is an Invalid Request Method i.e. Apart from 'OPTIONS','PUT', 'DELETE', 'TRACE','CONNECT','HEAD', 'POST','GET'.
	- 400 Bad Request: Reason Invalid URL -> Error if URL is Invalid
	- 400 Bad Request: Reason Invalid Version -> Error if HTTP Version is Invalid
	- 404 Not Found -> Error if the requested URL is not found in 'document root directory - www'
	- 501 Not Implemented -> Error if the requested Method is 'OPTIONS','PUT', 'DELETE', 'TRACE','CONNECT','HEAD', 'POST' which is not implemented.
	- 500 Internal Server Error -> Error is there is something wrong with the ws.conf file.
o Port Number in ws.conf should be in between 1024 to 65535.

PERFORMANCE EVALUATION:

o Make sure the server is up and running.
o Use a Client.py to test the performance of the server.
o There are 100 HTML pages i.e. index1.html to index100.html in the www folder.
o With the help of multi-threading, client calls 100 HTML pages at the same time and calls 1 html page 100 times simultaneously.
o Server will print the start time, the end time and the time difference of the thread. 
o Along with the above process, when a page is requested from the browser, the server is able to serve that request simultaneously.
