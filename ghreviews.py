import re
from datetime import datetime
import configparser
import chromedriver
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
        print("GhReviews.__del__")
        self.cmn.scpPutFile(self.shostname, self.dbpath, self.spath, ow=False)
        self.cdriver.driver.quit()
        del self.dbm
        del self.cmn

    def __init__(self, dbm, basedir, rdbpath, cpath):
        self.backurls = []
        self.fronturls = []
        self.furl = ""
        self.curl = ""
        self.purl = ""
        self.ppurl = ""

        cp = configparser.ConfigParser()
        cp.read(cpath, encoding='utf-8')
        self.cp = cp
        self.xpath = cp['xpath']
        self.url = cp['default']['url']
        self.saveim = int(cp['default']['save_interval_minutes'])
        print("save interval minutes:",self.saveim)
        sdomain = urlparse(self.url).netloc.replace('.','')

        self.dbm = dbm
        dbmcur = dbm.cur
        stsp =  basedir + "/sql/tables" # should be env
        with open(stsp + "/reviews.sql.tpl", 'r', encoding='utf-8') as f:
          tt = string.Template(f.read())
          result = tt.safe_substitute({'sdomain':sdomain})
          print("read sql:",result)
          dbmcur.execute(result)
        self.rtn = sdomain + "_reviews"
      
        cdriver = chromedriver.ChromeDriver()
        self.cdriver = cdriver
        self.driver = cdriver.driver
        self.cut = time.time()
        try:
          sim = int(os.getenv('SYNC_INTERVAL_MINUTES'))
        except Exception as ex:
          print("catch Exception to get SYNC_INTERVAL_MINUTES, set to 20 minutes default:", ex)
          sim = 20
        self.sim = sim
        print("sync interval minutes:",sim)
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

    def srcScrape(self, srcurl, retry=0, nexts=True):
        print("start scrape(srcurl,retry,nexts):",srcurl,retry,nexts)
        try:
          doc = self.cdriver.get_doc(srcurl)
          while True:
            for i in range(3):
              try:
                if self.curl != self.driver.current_url:
                  break
              except Exception as ex:
                print("catch Exception in get  self.driver.current_url:",ex)
              print("get self.driver.current_url:i:",i)
              time.sleep((i+1)*1)
            if self.curl == self.driver.current_url:
              print("retry over(i,self.curl):",i,self.curl)
              if retry < 3:
                print("retry for same curl:",retry)
                curl = self.curl
                self.curl = ""
                return self.srcScrape(curl, retry+1)
            self.ppurl = self.purl
            self.purl = self.curl
            self.curl = self.driver.current_url
            #print("furl:",self.furl,",curl:",self.curl,",purl:",self.purl,",ppurl:",self.ppurl,",fronturls:",self.fronturls)
            #if self.curl in [self.furl] or self.curl in self.fronturls:
            if self.curl in self.fronturls:
              print("self.curl in self.fronturls")
              return
            #print("after self.curl in [self.furl] || self.curl in self.fronturls")
            if self.furl == "":
              self.furl = self.driver.current_url
            #print("before items = self.driver.find_elements(By.XPATH, self.xpath['items'])")
            items = self.driver.find_elements(By.XPATH, self.xpath['items'])
            if len(items) == 0:
              if retry < 3:
                print("retry for len(items) == 0:",retry)
                curl = self.curl
                self.curl = ""
                return self.srcScrape(curl, retry+1)
              print("failed for len(items) == 0")
              return
            ds = []
            #print("before if not self.driver.current_url in self.fronturls:")
            if not self.driver.current_url in self.fronturls:
              #print("after if not self.driver.current_url in self.fronturls:")
              for item in items:
                #print("start item:",item)
                d = {'reviews': 0, 'score': 0, 'rank': 0, 'name': '', 'desc':'', 'surl':self.curl}
                es = item.find_elements(By.XPATH, self.xpath['score'])
                if len(es) > 0:
                  d['score'] = common_library.CommonLibrary.getNumberFromString(es[0].get_attribute('innerHTML'))
                es = item.find_elements(By.XPATH, self.xpath['name'])
                d['name'] = es[0].text # required
                #print("before option")
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
                #print("after option")
                cd = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                #self.dbm.cur.execute("select count(*) from "+self.rtn)
                self.dbm.cur.execute("select count(*) from (select count(*) as c FROM "+self.rtn+" group by name) as x")
                count = self.dbm.cur.fetchone()[0]
                self.dbm.cur.execute("select created from "+self.rtn+" where name = ? order by id desc", (d["name"],))
                fo = self.dbm.cur.fetchone()
                if fo is not None:
                  created = fo[0]
                  if count is not None and count > 0:
                    cut = time.time()
                    dtcreated = datetime.strptime(created, '%Y-%m-%d %H:%M:%S')
                    tscreated = datetime.timestamp(dtcreated)
                    diff = self.saveim*60 - (cut -tscreated)
                    sdiff = int(diff / count)
                    if diff > 0:
                      print(created,cut,dtcreated,tscreated)
                      if sdiff >= 1:
                        print("wait sdiff for ",d["name"],":",sdiff," seconds...")
                        time.sleep(sdiff)
                        print("append to backurls:",self.driver.current_url)
                        self.backurls.append(self.driver.current_url)
                        break
                        #for i in range(count):
                        #  print("wait for ",d["name"],":",sdiff,"(",i,") seconds...")
                      else:
                        print("wait for ",d["name"],":",diff," seconds...")
                        time.sleep(diff)
                print("before insert into:",d)
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
              if not self.driver.current_url in self.backurls:
                print("append to fronturls:",self.driver.current_url)
                self.fronturls.append(self.driver.current_url)
            print("before if nexts:",nexts)
            if nexts:
              es = self.driver.find_elements(By.XPATH, self.xpath['next'])
              print("next(self.xpath['next'],es):",self.xpath['next'],es)
              if len(es) > 0:
                es[0].click()
              else:
                print("return: len(es) > 0 else ")
                return
            retry = 0 # because finish
        except Exception as ex:
          cdriver = chromedriver.ChromeDriver()
          self.cdriver = cdriver
          self.driver = cdriver.driver
          print("catch Exception in try:",ex)
          time.sleep((retry+1)*60)
          if retry < 3:
            if self.curl == "":
              if self.purl == "":
                if self.ppurl == "":
                  if self.furl == "":
                    return
                  curl = self.furl
                else:
                  curl = self.ppurl
              else:
                curl = self.purl
            else:
              curl = self.curl
            self.curl = ""
            print("retry for get_doc(retry,curl):",retry,curl)
            return self.srcScrape(curl, retry+1)
