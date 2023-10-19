import threading
import time
import requests
import socket
from bs4 import BeautifulSoup
from urllib.parse import urlparse

class SafeList:
    '''This SafeList class is protected by a mutex, it stores a queue of URLs to be visited'''
    def __init__(self):
        self.list = []
        self.mutex = threading.Lock()

    def batch_insert(self, item_list):
        with self.mutex:
            self.list.extend(item_list)

    def pop(self):
        with self.mutex:
            return self.list.pop()
    
    def isEmpty(self):
        return len(self.list) == 0
        
class SafeMap:
    '''This SafeMap class has protected access by a mutex, it stores all visited domains'''
    def __init__(self):
        self.map = {}
        self.mutex = threading.Lock()
    
    def batch_insert(self, item_list):
        with self.mutex:
            for item in item_list:
                self.map[item] = 0

    def check(self, item):
        return item in self.map

class Site:
    '''This is a class wrapper for a website and the information required by the assignment'''
    def __init__(self, url, ip, geolocation, resp_time):
        self.url = url
        self.ip = ip
        self.geolocation = geolocation
        self.response_time = resp_time

class SafeWriter:
    '''This is a SafeWriter that utilizes a mutex to lock access to the file "scraped.txt"'''
    def __init__(self):
        self.mutex = threading.Lock()

    def write(self, s: Site):
        with self.mutex:
            with open("scraped.txt", "a") as f:
                f.write("{},{},{},{}\n".format(s.response_time, s.geolocation, s.ip, s.url))

def get_location(ip):
    '''This function utilizes the ip-api API to find geolocation of ips. 
       Might have chance of denial of service due to too high request rate'''
    if ip == "":
        return "Country Not Found"
    attempt = 0
    country = None
    # try 3 times
    while country is None and attempt < 3:
        if attempt > 0:
            time.sleep(3)
        try:
            #response = requests.get(f'https://ipapi.co/{ip}/json/', timeout=5).json()
            response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5).json()
            country = response.get("country_name")
        except:
            print("Either timeout or faulty response")
        attempt += 1

    if country:
        return country
    else:
        return "Country Not Found"

def get_ip(url: str):
    '''This function returns the ip address of the url'''
    url = url.replace("https://", "", 1)
    url = url.replace("http://", "", 1)
    ip = socket.gethostbyname(url)
    return ip

def scrapper(ls: SafeList, m: SafeMap, w: SafeWriter):
    '''This is the main scrapper logic to be run on threads.
       They share the same SafeList, SafeMap and SafeWriter'''
    while not ls.isEmpty():
        url = ls.pop()
        start = time.time()
        try:
            print(url)
            resp = requests.get(url, timeout=5)
            time_taken = str(round((time.time() - start), 2))
            ip = get_ip(url)
            location = get_location(ip)
        except:
            print("Erroneous url: {}".format(url))
        newUrls = []
        soup = BeautifulSoup(resp.content, "html.parser")
        links = soup.select("a[href]")
        for link in links:
            url_string = link['href']
            parsed = urlparse(url_string)
            if parsed.scheme == "" or parsed.scheme is None:
                continue
            if parsed.hostname == "" or parsed.hostname is None:
                continue
            url_string = "{}://{}".format(parsed.scheme, parsed.hostname) 
            # print(url_string)
            if not m.check(url_string) and url_string not in newUrls:
                newUrls.append(url_string)
        m.batch_insert(newUrls)
        ls.batch_insert(newUrls)
        w.write(Site(url, ip, location, time_taken))
        time.sleep(2)

if __name__ == '__main__':
    ls = SafeList()
    m = SafeMap()
    w = SafeWriter()
    # Initialize and read from a file of urls
    with open("initial.txt", "r") as f:
        urls = f.read().splitlines()
        ls.batch_insert(urls)
        m.batch_insert(urls)

    # initialize threads and start them
    threadList = []
    for i in range(3):
        thread = threading.Thread(target=scrapper, args=(ls, m, w))
        threadList.append(thread)

    for td in threadList:
        td.start()
    
    for td in threadList:
        td.join()