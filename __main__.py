#! /usr/bin/env python3

import traceback
import os.path

from __init__ import *

sh = TweetShell()

for line in open(os.path.expanduser('~/.twshellrc')):
  sh.onecmd(line)

while True:
  try:
    sh.cmdloop()
  except KeyboardInterrupt:
    print()
  except Exception as e:
    traceback.print_exc()
