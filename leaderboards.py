import sys
import os
import platform

import ac

if platform.architecture()[0] == "64bit":
  ac.log("1")
  sysdir = "stdlib64"
else:
  ac.log("2")
  sysdir = "stdlib"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), sysdir))
os.environ['PATH'] = os.environ['PATH'] + ";."

from leaderboards_lib.leaderboards_lib import leaderboards_app

def acMain(ac_version):
  return leaderboards_app.acMain(ac_version)

def acUpdate(deltaT):
  leaderboards_app.acUpdate(deltaT)

def acShutdown():
  leaderboards_app.acShutdown()