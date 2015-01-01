#! /usr/bin/env python3

import traceback

from __init__ import *

sh = TweetShell()

while True:
  try:
    sh.cmdloop()
  except KeyboardInterrupt:
    print()
  except Exception as e:
    traceback.print_exc()
