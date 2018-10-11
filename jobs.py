import requests
from bs4 import BeautifulSoup
import os
import urllib.request
import re
from jobqueue import JOBQUEUE
from threading import Lock

lock = Lock()

class RestrictedUrl(object):
    """ Create complete url and check url whether it was visited """

    visited_urls = {}
    base_url = "exponea.com"

    def __init__(self, dest_url, src_url):
        self.valid = True
        self.url = None

        if dest_url is None:
            self.valid = False
            return

        # if begins with /, added src_url
        if re.search('^/', dest_url) is not None:
            self.url = src_url + dest_url
        else:
            self.url = dest_url

        if re.search("^http", self.url) is None:
            self.valid = False
            return

        if RestrictedUrl.base_url not in dest_url:
            self.valid = False
            return

        with lock:
            if self.url in RestrictedUrl.visited_urls:
                self.valid = False
                return

            RestrictedUrl.visited_urls[self.url] = 1


class Job(object):
    """ Base class for all jobs that will be done by threads """

    def do_my_job(self):
        raise NotImplemented

    def __lt__(self, other):
        return self.priority < other.priority

    def __eq__(self, other):
        return self.priority == other.priority


class VisitJob(Job):

    def __init__(self, url):
        self.url = url
        self.priority = 100
        assert self.url is not None, "Has to be URL!"

    def do_my_job(self):
        r = requests.get(self.url)
        data = r.text
        soup = BeautifulSoup(data)
        for a in soup.find_all('a'):
            r_url = RestrictedUrl(dest_url=a.get("href"), src_url=self.url)
            if r_url.valid: JOBQUEUE.put(VisitJob(url=r_url.url)) 
        for img in soup.find_all('img'):
            r_url = RestrictedUrl(dest_url=img.get("src"), src_url=self.url)
            if r_url.valid: JOBQUEUE.put(DownloadJob(url=r_url.url))


class DownloadJob(Job):

    destfolder = "./"

    def __init__(self, url):
        self.url = url
        self.priority = 0
        assert self.url is not None, "Has to be URL!"

    def do_my_job(self):
        # change it to a different way if you require
        name = self.url.split('/')[-1]
        dest = os.path.join(DownloadJob.destfolder, name)
        assert isinstance(dest, str), f"Should be str, is {str.__class__}"
        urllib.request.urlretrieve(self.url, dest)
