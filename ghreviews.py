import re
from datetime import datetime
import configparser
import common_library
import time
import os
import string
import inspect
from lxml import html as lxmlhtml
import html
from lxml import etree
from urllib.parse import urlparse
import emoji
from selenium.webdriver.common.by import By

class GhReviews:
    def __del__(self):
        print("DsFeed.__del__")
        self.cmn.scpPutFile(self.shostname, self.dbpath, self.spath, ow=False)
        self.cdriver.driver.quit()
        del self.dbm
        del self.cmn

    def __init__(self, dbm, cdriver, basedir, rdbpath, cpath, sdomain):
        self.furl = ""
        self.curl = ""
        self.purl = ""
        self.ppurl = ""

        cp = configparser.ConfigParser()
        cp.read(cpath, encoding='utf-8')
        self.cp = cp
        self.xpath = cp['xpath']

        self.dbm = dbm
        dbmcur = dbm.cur
        stsp =  basedir + "/sql/tables" # should be env
        with open(stsp + "/reviews.sql.tpl", 'r', encoding='utf-8') as f:
          tt = string.Template(f.read())
          result = tt.safe_substitute({'sdomain':sdomain})
          print("read sql:",result)
          dbmcur.execute(result)
        self.rtn = sdomain + "_reviews"
      
        self.cdriver = cdriver
        self.driver = cdriver.driver
        self.cut = time.time()
        try:
          sim = int(os.getenv('SYNC_INTERVAL_MINUTES'))
        except Exception as ex:
          print("catch Exception to get SYNC_INTERVAL_MINUTES, set to 20 minutes default:", ex)
          sim = 20
        self.sim = sim
        print("sim:",sim)
        self.basedir = basedir
        self.dbpath =  self.basedir + "/ghreviews.db"
        self.shostname = os.getenv('SYNC_HOSTNAME')
        self.spath = os.getenv('SYNC_PATH')
        self.cmn = common_library.CommonLibrary(self.shostname)
        if rdbpath != "":
          print("overwrite db(rdbpath,syncpath):",rdbpath,self.spath)
          self.cmn.scpPutFile(self.shostname, rdbpath, self.spath)
        self.cmn.scpGetFile(self.shostname, self.spath, self.dbpath)

    def saveDriver(self, fn):
        logdir = os.getenv('LOG_DIR', self.basedir+"/log")
        if not os.path.exists(logdir):
          return
        dt = datetime.now().strftime("%Y%m%d%H%M%S")
        path = logdir + "/" + fn + "___" + dt
        try:
          self.driver.save_screenshot(path + ".png")
          with open(path + ".html", "w") as f:
              f.write(self.driver.page_source)
        except Exception as ex:
          print("catch Exception in saveDriver:",ex)

    def srcScrape(self, srcurl):
        doc = self.cdriver.get_doc(srcurl)
        while True:
          for i in range(3):
            if self.curl != self.driver.current_url:
              break
            time.sleep((i+1)*1)
          if self.curl == self.driver.current_url:
            print("retry over:",i)
          self.ppurl = self.purl
          self.purl = self.curl
          self.curl = self.driver.current_url
          print("furl:",self.furl,",curl:",self.curl,",purl:",self.purl,",ppurl:",self.ppurl)
          if self.curl in [self.purl, self.ppurl, self.furl]:
            print("return: self.curl in [self.purl, self.ppurl, self.furl]")
            return
          if self.furl == "":
            self.furl = self.driver.current_url
          items = self.driver.find_elements(By.XPATH, self.xpath['items'])
          if len(items) == 0:
            print("return:  len(items) == 0")
            return
          ds = []
          for item in items:
            d = {'reviews': 0, 'score': 0, 'rank': 0, 'name': '', 'desc':'', 'surl':self.curl}
            es = item.find_elements(By.XPATH, self.xpath['score'])
            if len(es) > 0:
              d['score'] = common_library.CommonLibrary.getNumberFromString(es[0].get_attribute('innerHTML'))
            es = item.find_elements(By.XPATH, self.xpath['name'])
            d['name'] = es[0].text # required
            # option
            if self.cp.has_option('xpath', 'reviews'):
              if self.xpath['reviews']:
                es = item.find_elements(By.XPATH, self.xpath['reviews'])
                if len(es) > 0:
                  d['reviews'] = common_library.CommonLibrary.getNumberFromString(es[0].get_attribute('innerHTML'))
            if self.cp.has_option('xpath', 'rank'):
              if self.xpath['rank']:
                es = item.find_elements(By.XPATH, self.xpath['rank'])
                if len(es) > 0:
                  d['rank'] = common_library.CommonLibrary.getNumberFromString(es[0].get_attribute('innerHTML'))
            if self.cp.has_option('xpath', 'desc'):
              if self.xpath['desc']:
                es = item.find_elements(By.XPATH, self.xpath['desc'])
                if len(es) > 0:
                  d['desc'] = es[0].text
            cd = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.dbm.cur.execute(
                "insert into "+self.rtn+" (reviews, score, rank, name, desc, surl, created, updated) \
                        values (?, ?, ?, ?, ?, ?, ?, ?)",
                (d['reviews'], d['score'], d['rank'], d['name'], d['desc'], d['surl'], cd, cd)
            )
            self.dbm.conn.commit()
            nut = time.time()
            if nut > self.cut+self.sim*60:
              self.cmn.scpPutFile(self.shostname, self.dbpath, self.spath, ow=False)
              self.cut = nut
          # end of for items 
          es = self.driver.find_elements(By.XPATH, self.xpath['next'])
          print("next(self.xpath['next'],es):",self.xpath['next'],es)
          if len(es) > 0:
            es[0].click()
          else:
            print("return: len(es) > 0 else ")
            return
        #doc = ' '.join(doc.splitlines())
        #doc = doc.replace("<![CDATA[", "").replace("]]>", "")
       
