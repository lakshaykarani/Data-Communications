#Author: Lakshay Karani lakshay.karani@colorado.edu
Proxy Contents: webproxy.py, cache folder		
#purpose: To Create a HTTP Based Web proxy Server that caches the requested URL in the local machine; to implement link Prefetching of the Requested URL
#Python version: 3.5.1

BEFORE RUNNING THE HTTP BASED WEB SERVER:

o Make sure while Running the proxy server you specify the Port Number and Maximum cache time.
	Example: webproxy.py [PORT NUMBER] [Max Cache Time]
	- Port Number should be an integer in between 5000 - 65535
	-MaxCacheTime should be an integer in seconds
	
o Change the proxy settings of your web browser. 
	- In Mozilla FireFox, Options --> Addvanced --> Network --> Connection Settings
	- Check Manual Proxy Configuation --> Set HTTP Proxy as 127.0.0.1 --> Port Number as you specified on Command Line.
	- Untick "Use this proxy for all protocols".
	
o Sample Websites that can run on this proxy.
	- http://ngn.cs.colorado.edu/
	- http://morse.colorado.edu/
	- http://stackoverflow.com/


TO RUN THE SERVER:

o Open the command prompt and run webproxy.py
o By default, Server is running on 127.0.0.1.
o You have to specify a Port Number and Max Cache Time.
o Example: webproxy.py [PORT NUMBER] [Max Cache Time]
o Open Mozilla FireFox and try to access any HTTP Website
o The Proxy Server is only capable of serving GET Requests as of now.
o It is compatible with HTTP/1.1 and HTTP/1.0
o Port Number in ws.conf should be in between 5000 to 65535.

o The URL that you access from the server is stored in "cache/" folder.
o If the internet connection is down and max cache time is less than the modified time, You will be able to view the Requested web Page

LINK PREFETCHING:

o When you access a URL, the proxy server will prefetch all the links from that URL and store it in Cache.
o So when you to try to access a link from that URL the proxy server will fetch that from the Cache.
o This will reduce the requesting time to fetch the URL.
