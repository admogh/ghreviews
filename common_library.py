import json
import re
import urllib
import os
import requests
import inspect
from lxml import html
import scp
import paramiko

class CommonLibrary:
  def __init__(self, remoteHost=None):
    if remoteHost is not None and remoteHost != "":
      config_file = os.path.join(os.getenv('HOME'), '.ssh/config')
      ssh_config = paramiko.SSHConfig()
      ssh_config.parse(open(config_file, 'r'))
      lkup = ssh_config.lookup(remoteHost)
      self.ssh = paramiko.SSHClient()
      self.ssh.load_system_host_keys()
      self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy) # sftp
      try:
        self.ssh.connect(
            lkup['hostname'],
            username=lkup['user'],
            port=lkup['port'],
            key_filename=lkup['identityfile'],
        )
        self.ssh_hostname = lkup['hostname']
        self.ssh_user = lkup['user']
        self.ssh_port = lkup['port']
        self.ssh_identityfile = lkup['identityfile']
        self.scp = scp.SCPClient(self.ssh.get_transport())
        # sftp
        self.sftp = self.ssh.open_sftp()
      except Exception as ex:
        # paramiko.ssh_exception.SSHException: Error reading SSH protocol banner
        print("catch exception in CommonLibrary.__init__:", ex)

  def scpGetFile(self, host, src, dst):
    print(host, src, dst)
    if hasattr(self, "scp"):
      try:
        rst = 0
        lst = 0
        # get ts
        paths = src.split('/')
        pathdir = ""
        for ipath in range(len(paths)):
          if ipath == len(paths) - 1:
            break
          if pathdir != "":
            pathdir = pathdir + '/'
          pathdir = pathdir + paths[ipath]
        print(paths, pathdir)
        if pathdir == '~':
          pathdir = "/home/" + self.ssh_user
        self.sftp.chdir(pathdir)
        attrs = self.sftp.stat(paths[len(paths)-1])
        rst = attrs.st_mtime
        if os.path.isfile(dst):
          lst = os.stat(dst).st_mtime
        if rst > lst:
          self.scp.get(src, dst)
      except scp.SCPException as ex:
        # Assumed that No such file or directory and ignored
        print(ex)

  # src is local, dst is remote
  def scpPutFile(self, host, src, dst, ow=True):
    if hasattr(self, "scp"):
      try:
        if ow==False:
          rst = 0
          lst = 0
          # get ts
          paths = dst.split('/')
          pathdir = ""
          for ipath in range(len(paths)):
            if ipath == len(paths) - 1:
              break
            if pathdir != "":
              pathdir = pathdir + '/'
            pathdir = pathdir + paths[ipath]
          print(paths, pathdir)
          if pathdir == '~':
            pathdir = "/home/" + self.ssh_user
          self.sftp.chdir(pathdir)
          attrs = self.sftp.stat(paths[len(paths)-1])
          rst = attrs.st_mtime
          if os.path.isfile(src):
            lst = os.stat(src).st_mtime
          print("src,dst,rst,lst:",src,dst,rst,lst)
          if lst <= rst:
            print("not put file for old(lst,rst):",lst,rst)
            return
        self.scp.put(src, dst)
        print("scpPutFile completed(src,dst):",src,dst)
      except scp.SCPException as ex:
        print("catch scp.SCPException in scpPutFile:", ex)
        return

  def __del__(self):
    if hasattr(self, "scp"):
      self.scp.close()
      self.ssh.close()

  @staticmethod
  def getNumberFromString(str):
    str = str.replace(',','')
    m1 = re.search("[^0-9\.]", str) # str
    m2 = re.search("[0-9\.]", str)  # num
    ret = ""
    if m1 and m2:
      if m1.start() > m2.start():
        ret = str[:m1.start()]
      else:
        ret = str[m2.start():]
        m3 = re.search("[^0-9\.]", ret)
        if m3:
          ret = ret[:m3.start()]
    elif m1:
      # only str
      ret = ""
    elif m2:
      # only num
      ret = str
    return ret

  @staticmethod
  def getSrcLocationString():
      frame = inspect.currentframe().f_back
      s = os.path.basename(frame.f_code.co_filename).replace('.', '_')
      s = s + "__" + frame.f_code.co_name
      s = s + "__" + str(frame.f_lineno)
      return s
  @staticmethod
  def toDiscord(whurl, msg):
      mc = {
          "content": msg
      }
      requests.post(whurl, mc)
      return
      rh = {'Content-Type': 'application/json'} #;charset=utf-8'}
      rd = json.dumps({"content": msg}).encode("utf-8")
      req = urllib.request.Request(
              whurl, rd, 
              {"User-Agent": "curl/7.64.1", "Content-Type" : "application/json"},
              method='POST', headers=rh)
      try:
          with urllib.request.urlopen(req) as response:
              body = json.loads(response.read())
              headers = response.getheaders()
              status = response.getcode()
              print(headers)
              print(status)
              print(body)
      except urllib.error.URLError as e:
           print(e.reason)
