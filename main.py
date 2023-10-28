import threading
import time
import requests
import socket
from bs4 import BeautifulSoup
from urllib.parse import urlparse


class SafeList:
    """
    This SafeList class is protected by a mutex, it stores a queue of URLs to be visited
    """
    def __init__(self, limit):
        self.list = []
        self.limit = limit
        self.count = 0
        self.mutex = threading.Lock()

    def insert(self, item):
        with self.mutex:
            if self.count >= self.limit:
                return
            self.count += 1
            self.list.append(item)

    def batch_insert(self, item_list):
        with self.mutex:
            self.count += len(item_list)
            self.list.extend(item_list)

    def pop(self):
        with self.mutex:
            return self.list.pop(0)

    def is_empty(self):
        return len(self.list) == 0


class SafeSet:
    def __init__(self, limit):
        self._set = set()
        self.limit = limit
        self.count = 0
        self.mutex = threading.Lock()

    def batch_insert(self, item_list):
        with self.mutex:
            for item in item_list:
                self.count += 1
                self._set.add(item)

    def insert(self, item):  
        with self.mutex:
            if self.count >= self.limit:
                return
            self.count += 1
            self._set.add(item)

    def contains(self, item):
        return item in self._set


class Site:
    """
    This is a class wrapper for a website and the information required by the assignment
    """
    def __init__(self, url, ip, geolocation, resp_time):
        self.url = url
        self.ip = ip
        self.geolocation = geolocation
        self.response_time = resp_time


class Scrapper:
    def __init__(self, id, safe_set: SafeSet, safe_list: SafeList):
        self.safe_set = safe_set
        self.safe_list = safe_list
        self.id = id

        with open("scraped.txt", "w") as f:
            f.write("")

    def write(self, s: Site):
        mutex = threading.Lock()
        with mutex:
            with open("scraped.txt", "a") as f:
                f.write(f"{s.response_time}, {s.geolocation}, {s.ip}, {s.url}\n")

    def get_ip(self, url: str):
        """
        This function returns the ip address of the url
        """
        hostname = urlparse(url).hostname
        ip = socket.gethostbyname(hostname)
        return ip

    def get_location(self, ip):
        """
        This function utilizes the ip-api API to find geolocation of ips.
        Might have chance of denial of service due to too high request rate
        """
        if ip == "":
            return "Country Not Found"

        country = None
        # try 3 times
        for _ in range(3):
            try:
                response = requests.get(f"http://ip-api.com/json/{ip}").json()

                if response.get("status") != "success":
                    print(response)
                    continue
            except Exception as e:
                print(e)
                continue
            country = response.get("country")

            if country:
                return country
            time.sleep(1)

        return "Country Not Found"

    def run(self):
        """
        This is the main scrapper logic to be run on threads.
        They share the same SafeList and SafeSet
        """

        while not self.safe_list.is_empty():
            url = self.safe_list.pop()

            start = time.time()
            try:
                print(f"scrapper: {self.id} scrapping {url}")
                resp = requests.get(url)
            except Exception as e:
                print(f"Erroneous url: {url}")
                print(e)
                continue

            time_taken = str(round((time.time() - start), 2))
            ip = self.get_ip(url)
            location = self.get_location(ip)
            self.write(Site(url, ip, location, time_taken))

            soup = BeautifulSoup(resp.content, "html.parser")
            links = soup.select("a[href]")
            for link in links:
                url_string = link["href"]
                parsed = urlparse(url_string)
                if parsed.hostname == "" or parsed.hostname is None:
                    continue

                if parsed.scheme == "" or parsed.scheme is None:
                    continue

                if not self.safe_set.contains(url_string):
                    self.safe_set.insert(url_string)
                    self.safe_list.insert(url_string)

            time.sleep(2)


def main():
    LIMIT = 3000
    safe_set = SafeSet(LIMIT)
    safe_list = SafeList(LIMIT)

    number_threads = 3
    thread_list = []

    # Initialize and read from a file of urls
    with open("initial.txt", "r") as f:
        urls = f.read().splitlines()
        safe_list.batch_insert(urls)
        safe_set.batch_insert(urls)

    # initialize threads and start them
    for id in range(number_threads):
        scrapper = Scrapper(id, safe_set, safe_list)
        thread = threading.Thread(target=scrapper.run)
        thread_list.append(thread)

        thread.start()


if __name__ == "__main__":
    main()
