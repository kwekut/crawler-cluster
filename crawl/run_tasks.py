from browser import start_crawling
from clusterer import start_clustering
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.events import JobEvent, EVENT_JOB_MISSED, EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from datetime import datetime, timedelta
import logging
from logging import getLogger
import uuid
# just use octoparse
logger = getLogger(__name__)
logging.basicConfig()
executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}
if __name__ == '__main__':

	def job_start():
		urls = open('urls_list.txt').read().split('\n')
		print('Task urls:', urls)
		logger.info('Task urls:', urls)
		cummulator = []
		topics = []
		images = []
		uris = []
		publishers = []
		categories = []
		batchid = str(uuid.uuid4())
		for i,url in enumerate(urls):
			if "=" in url:
				pub,cat,uri = url.replace('"', "").split("=")
				ur = uri.strip("',\n")
				data = start_crawling(pub,cat,ur)
				for pb,ct,ur,tp,im in data:
					#clean out default links and unavailables
					#no topic with less than 4 words has contex
					if len(tp.split(" ")) > 4:
						cummulator.append((str(pb),str(ct),str(ur),str(tp),str(im)))
						# print('cummulator',cummulator)
		for pb,ct,ur,tp,im in cummulator:
			publishers.append(str(pb))
			categories.append(str(ct))
			uris.append(str(ur))
			topics.append(str(tp))
			images.append(str(im))
		#make sure they are all on the same index number wavelength
		if len(cummulator) == len(topics) == len(uris) == len(publishers) == len(images) == len(categories):
			result = start_clustering(batchid,cummulator,topics,uris,publishers)
			print('Clustering result:',result)
			logger.info('Clustering result:',result)
		else:
			print('Crawl Error ====>  Index not matching:',cummulator)

	def my_listener(event):
		if event.exception:
		    print('The job crashed :(')
		else:
		    print('The job worked :)')

	delayStart = datetime.now() + timedelta(seconds=30)
	scheduler = BlockingScheduler()
	# scheduler.configure(executors=executors, job_defaults=job_defaults)
	scheduler.add_job(job_start, 'interval', start_date=delayStart, minutes=30)
	scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
	scheduler.start()