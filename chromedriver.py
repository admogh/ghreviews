from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
import time
import random
from urllib.parse import urlparse
from webdriver_manager.chrome import ChromeDriverManager 

class ChromeDriver:
    def __init__(self):
        user_agent = [
                #'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
                #'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
                #'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36',
                #'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'
        ]
        #PROXY = "160.19.232.85:3128"
        #webdriver.DesiredCapabilities.CHROME['proxy'] = {
        #    "httpProxy": PROXY,
        #    "ftpProxy": PROXY,
        #    "sslProxy": PROXY,
        #    "proxyType": "MANUAL",
        #}
        #webdriver.DesiredCapabilities.CHROME['acceptSslCerts'] = True
        chrome_option = webdriver.ChromeOptions()
        chrome_option.add_argument('--headless')
        chrome_option.add_argument('--disable-gpu')
        chrome_option.add_argument('--disable-infobars')
        chrome_option.add_argument('--disable-dev-shm-usage')
        chrome_option.add_argument('--disable-extentions')
        chrome_option.add_argument('--no-sandbox')
        #chrome_option.add_argument('--disable-infobars')
        chrome_option.add_argument(
            '--user-agent=' + user_agent[random.randrange(0, len(user_agent), 1)])
        self.driver = webdriver.Chrome(ChromeDriverManager().install(),chrome_options=chrome_option)
        self.driver.set_page_load_timeout(60)
    def __del__(self):
        self.driver.quit()
    def wait_scroll(self, tn, sn=0, lasten=0):
        WebDriverWait(self.driver, 120).until(EC.visibility_of_element_located((By.TAG_NAME, tn)))
        for i in range(sn):
            elems_article = self.driver.find_elements_by_tag_name(tn)
            last_elem = elems_article[lasten]
            actions = ActionChains(self.driver);
            actions.move_to_element(last_elem);
            actions.perform();
        #self.driver.find_element_by_tag_name('body').click()
        #self.driver.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
        #self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
    def get_doc(self,url,retry=0):
        time.sleep(retry)
        try:
          self.driver.get(url)
        except TimeoutException as ex:
          print("catch selenium.common.exceptions.TimeoutException in get_doc:",ex)
          if retry >= 3:
            print("failed to retry get_doc, give up(url,retry):",url,retry)
            return ""
          return ChromeDriver.get_doc(self, url, retry+1)
        #srcdomain = urlparse(url).netloc
        #if srcdomain == "twitter.com":
        #    self.wait_scroll("article")
        #driver.implicitly_wait(10)
        return self.driver.page_source 
