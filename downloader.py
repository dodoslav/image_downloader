import sys, traceback
import os
import threading
import time
from jobs import DownloadJob, VisitJob

from jobqueue import JOBQUEUE


class DownloadThread(threading.Thread):
    def __init__(self, queue, name):
        super(DownloadThread, self).__init__()
        self.queue = queue
        self.name = name
        self.daemon = True

    def run(self):
        while self.queue.qsize() > 0:
            job = self.queue.get()
            print(f"[{self.name}] Job: {job.__class__} - url: {job.url}")
            try:
            	job.do_my_job()
            except Exception as e:
                print(f"[{self.name}] ERROR: Job: {job.__class__} - url: {job.url}: {e}")
                # traceback.print_exc(file=sys.stdout)
            self.queue.task_done()

class MonitorThread(threading.Thread):
	def __init__(self):
		super(MonitorThread, self).__init__()
		self.daemon = True

	def run(self):
		while True:
			time.sleep(5)
			print(f"JOBQUEUE size: {JOBQUEUE.qsize()}")


def download(url, destfolder="./", numthreads=6):
	DownloadJob.destfolder = destfolder
	JOBQUEUE.put(VisitJob(url=url))
	for i in range(numthreads):
		t = DownloadThread(JOBQUEUE, f"thread-{i}")
		t.start()

	t = MonitorThread()
	t.start()

	JOBQUEUE.join()

download("https://exponea.com", destfolder="./images")
