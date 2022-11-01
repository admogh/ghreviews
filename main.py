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
import chromedriver
import html
from dotenv import load_dotenv
load_dotenv()

usage = 'Usage: python {} [--surl <surl>] [--cpath <cpath>] [--rdb <rdb>] [--help]'\
        .format(__file__)
argparser = ArgumentParser(usage=usage)
argparser.add_argument('-su', '--surl', type=str,
                       dest='surl',
                       help='start url')
argparser.add_argument('-cp', '--cpath', type=str,
                       dest='cpath',
                       help='config path')
argparser.add_argument('-rd', '--rdb', type=str,
                       dest='rdb',
                       help='restore: overwrite remote db')
args = argparser.parse_args()

if not args.surl or not args.cpath:
  print("set surl and cpath, exit")
  exit()
surl = args.surl
cpath = args.cpath
sdomain = urlparse(surl).netloc.replace('.','')
print("sdomain:",sdomain)

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
cdriver = chromedriver.ChromeDriver()
cghreviews = ghreviews.GhReviews(dbm, cdriver, basedir, rdbpath, cpath, sdomain)

def getSrc(url):
    if re.match("^(http|https):(\/|\/\/|)", url) is None:
      url = "https://" + url
    print("getSrc: " + url)
    cghreviews.srcScrape(url)

try:
  getSrc(surl)
except KeyboardInterrupt:
  pass

del cghreviews
