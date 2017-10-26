from __future__ import absolute_import
import re
import os
import codecs
import time,requests
from datetime import datetime
from collections import defaultdict
import numpy as np
import pandas as pd
import nltk
import uuid
#import mpld3
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
import language_check
import itertools
from urllib import robotparser
from urllib import parse
from urllib.request import urlopen 
from htmldom import htmldom 
import lxml.html as LH
import lxml.html.clean as clean
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait

# firefox = webdriver.Remote(
#           command_executor='http://localhost:4444/wd/hub',
#           desired_capabilities=DesiredCapabilities.FIREFOX) 
#text = driver.find_element_by_xpath("/html/body/")
#text = driver.find_element_by_tag_name('body')
# allElements = driver.find_elements_by_xpath("//*")
# for i in allElements:
# 	topics.append(i.text)

def start_crawling(publisher,category,url):
	print('crawling begins :', url)
	Links = []
	Images = []
	baseUrl = url

	def url_to_text(urlList,sentences):
		default = "topic-unavailable"
		try:
			rankSentences = defaultdict(int)
			def parseUrl(liste, phrase):
				nonlocal rankSentences
				for uri in liste:
					if uri.lower() in phrase.lower():
						rankSentences[phrase] += 1
			for sentence in sentences:
				m = parseUrl(urlList, sentence)
			v=list(rankSentences.values())
			k=list(rankSentences.keys())
			sugg = k[v.index(max(v))]
			if rankSentences.get(sugg, 0) < 4:
				return default
			else:
				return sugg
		except:
			return default

	def url_to_image(urlList,images):
		default = "image-unavailable"
		try:
			rankImages = defaultdict(int)
			def parseUrl(liste, phrase):
				nonlocal rankImages
				for uri in liste:
					if uri.lower() in phrase.lower():
						rankImages[phrase] += 1
			for image in images:
				m = parseUrl(urlList, image)
			v=list(rankImages.values())
			k=list(rankImages.keys())
			sugg = k[v.index(max(v))]
			if rankImages.get(sugg, 0) < 2:
				return default
			else:
				return sugg
		except:
			return default

	# http://www.aptuz.com/blog/selenium-implicit-vs-explicit-waits/
	chromeDriver = webdriver.Remote(
	          command_executor='http://selenium-hub:4444/wd/hub',
	          desired_capabilities=DesiredCapabilities.CHROME)

	try:
		chromeDriver.get(baseUrl)
	except:
		try:
			print("Url TimeOut, trying again with increaed TimeOut ===>", baseUrl)
			chromeDriver.implicitly_wait(45)
			chromeDriver.get(baseUrl)
		except:
			print("Url TimeOut, ignore url ===>", baseUrl)
			callingfunction = useBSoup(baseUrl)
			pass
	#get topics -if not available via url
	texts = chromeDriver.find_element(By.TAG_NAME, "body").text
	Topics = texts.split("\n")
	#get images
	images = chromeDriver.find_elements_by_tag_name('img')
	for image in images:
		try:
			img = image.get_attribute('src')
			Images.append(img)
		except:
			pass
	#get urls their topics,images
	elems = chromeDriver.find_elements_by_xpath("//a[@href]")
	for elem in elems:
		try:
			href = elem.get_attribute("href")
			urils = href.split("-")
			print("href ===>", href)
			texti = elem.text
			if texti:
				imag = url_to_image(urils,Images)
				Links.append((publisher,category,href,texti,imag))
			else:
				imag = url_to_image(urils,Images)
				suggestion = url_to_text(urils,Topics)
				Links.append((publisher,category,href,suggestion,imag))
		except:
			try:
				print("Parse Error for ==>", str(href))
			except:
				print("Parse Error for ==>", str(elem))
	chromeDriver.quit()
	return Links


	# Combine with beautysoup for js websites
	# Backup option for Fortune et al
	def useBSoup(url):
		try:
			soup=BeautifulSoup(chromeDriver.page_source)
			for link in soup.find_all('a'):
				hrefi = link.get('href',"")
				urils = hrefi.split("-")
				texty = link.get_text()
				if texty:
					imag = url_to_image(urils,Images)
					Links.append((publisher,category,hrefi,texty,imag))
				else:
					imag = url_to_image(urils,Images)
					sugg = url_to_text(urils,Topics)
					Links.append((publisher,category,hrefi,sugg,imag))
		except:
			print("Parse Error for site ==>", url)
			pass

# # to introduce wait, if there are a lot of stale element reference: element is not attached to the page document
# # https://stackoverflow.com/questions/27003423/python-selenium-stale-element-fix
# 	def findUrl(driver):
# 	    element = driver.find_elements_by_id("data")
# 	    if element:
# 	        return element
# 	    else:
# 	        return False
# 	element = WebDriverWait(chromeDriver, 6).until(findUrl)




# def start_crawling_text(publisher,category,url):
# 	ignore_tags=('script','noscript','style')
# 	with contextlib.closing(webdriver.Firefox()) as browser:
# 		browser.get(url) # Load page
# 		content=browser.page_source
# 		cleaner=clean.Cleaner()
# 		content=cleaner.clean_html(content)    
# 		with open('/tmp/source.html','w') as f:
# 			f.write(content.encode('utf-8'))
# 		doc=LH.fromstring(content)
# 		with open('/tmp/result.txt','w') as f:
# 			for elt in doc.iterdescendants():
# 				if elt.tag in ignore_tags: continue
# 				text=elt.text or ''
# 				tail=elt.tail or ''
# 				words=' '.join((text,tail)).strip()
# 				if words:
# 					words=words.encode('utf-8')
# 					f.write(words+'\n') 

