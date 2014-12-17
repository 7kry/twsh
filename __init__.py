#! /usr/bin/env python3

import sys
import cmd

class TweetShell(cmd.Cmd):
  prompt = '(nologin)> '

  #def do_hoge(self, argstr):
  #  'HOGEHOGE'
  #  print(argstr)
  def do_EOF(self, *argv):
    sys.exit(0)
