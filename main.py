from argparse import ArgumentParser
import os
import re
import json
import time
import urllib.request
import requests
import sys
from lxml import html as lxmlhtml
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import lxml.etree as etree
from urllib.parse import urlparse
import ghreviews
import common_library
import sqlitemodel
import html
from dotenv import load_dotenv
load_dotenv()

usage = 'Usage: python {} [--cpath <cpath>] [--rdb <rdb>] [--help]'\
        .format(__file__)
argparser = ArgumentParser(usage=usage)
argparser.add_argument('-cp', '--cpath', type=str,
                       dest='cpath',
                       help='config path')
argparser.add_argument('-rd', '--rdb', type=str,
                       dest='rdb',
                       help='restore: overwrite remote db')
args = argparser.parse_args()

if not args.cpath:
  print("required argument not set , exit")
  exit()
cpath = args.cpath
#sdomain = urlparse(surl).netloc.replace('.','')
#print("sdomain:",sdomain)

rdbpath = ""
if args.rdb:
  if os.path.exists(args.rdb):
    rdbpath = args.rdb

basedir = os.path.dirname(os.path.abspath(__file__))
dbpath =  basedir + "/ghreviews.db"
shostname = os.getenv('SYNC_HOSTNAME')
spath = os.getenv('SYNC_PATH')
cmn = common_library.CommonLibrary(shostname)
if rdbpath != "":
  print("overwrite db(rdbpath,syncpath):",rdbpath,spath)
  cmn.scpPutFile(shostname, rdbpath, spath)
cmn.scpGetFile(shostname, spath, dbpath)

dbm = sqlitemodel.SqliteModel(dbpath)
cghreviews = ghreviews.GhReviews(dbm, basedir, rdbpath, cpath)

try:
  while True:
    print("start in main.py while True")
    cghreviews.backurls = []
    cghreviews.fronturls = []
    url = cghreviews.url
    if re.match("^(http|https):(\/|\/\/|)", cghreviews.url) is None:
      url = "https://" + cghreviews.url
    cghreviews.srcScrape(url)
    print("backurls start in main.py while True:",cghreviews.backurls)
    for backurl in cghreviews.backurls:
      print("backurl start in main.py while True:",backurl)
      cghreviews.srcScrape(backurl, nexts=False)
except KeyboardInterrupt:
  pass

del cghreviews
