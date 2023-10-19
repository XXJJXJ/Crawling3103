import threading
import time
import requests
import socket
from bs4 import BeautifulSoup
from urllib.parse import urlparse


class SafeList:
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
    def __init__(self, url, ip, geolocation, resp_time):
        self.url = url
        self.ip = ip
        self.geolocation = geolocation
        self.response_time = resp_time


class SafeWriter:
    def __init__(self):
        self.mutex = threading.Lock()

    def write(self, s: Site):
        with self.mutex:
            with open("scraped.txt", "a") as f:
                f.write(
                    "{},{},{},{}\n".format(s.response_time, s.geolocation, s.ip, s.url)
                )


def get_location(ip):
    if ip == "":
        return "Country Not Found"
    attempt = 0
    country = None
    # try 5 times
    while country is None or attempt < 5:
        response = requests.get(f"https://ipapi.co/{ip}/json/").json()
        country = response.get("country_name")
        attempt += 1

    if country:
        return country
    else:
        return "Country Not Found"


def get_ip(url: str):
    url = url.replace("https://", "", 1)
    url = url.replace("http://", "", 1)
    ip = socket.gethostbyname(url)
    return ip


def scrapper(ls: SafeList, m: SafeMap, w: SafeWriter):
    while not ls.isEmpty():
        url = ls.pop()
        start = time.time()
        try:
            print(url)
            resp = requests.get(url)
            time_taken = str(round((time.time() - start), 2))
            ip = get_ip(url)
            location = get_location(ip)
        except:
            print("Erroneous url: {}".format(url))
        newUrls = []
        soup = BeautifulSoup(resp.content, "html.parser")
        links = soup.select("a[href]")
        for link in links:
            url_string = link["href"]
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


if __name__ == "__main__":
    ls = SafeList()
    m = SafeMap()
    w = SafeWriter()
    # Initialize and read from a file of urls
    with open("initial.txt", "r") as f:
        urls = f.read().splitlines()
        ls.batch_insert(urls)
        m.batch_insert(urls)

    # print("Starting URLs:\n")
    # print(urls)
    # initialize threads and start them
    threadList = []
    for i in range(3):
        thread = threading.Thread(target=scrapper, args=(ls, m, w))
        threadList.append(thread)

    for td in threadList:
        td.start()

    for td in threadList:
        td.join()
