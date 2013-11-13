#! /usr/bin/env python2

import sys
import os
import re
import tweepy
import readline
import pprint

DEFAULT_AUTHFILE = os.path.expanduser("~") + "/.twitter_auth"
readline.parse_and_bind('tab: complete')

class TweetShell:
	def __init__(self, authfile):
		self.__authfile = authfile
		a = map(lambda l: re.compile("^(.*?)(//.*)?$").search(l.strip()).group(0).rstrip().split(),
		        open(self.__authfile))
		a = filter(lambda l: len(l) == 5, a)
		self.__auth = {}
		for t in a:
			if t[0] in self.__auth:
				sys.exit("Duplicated screen_name in the authfile.")
			self.__auth[t[0]] = tweepy.OAuthHandler(t[1], t[2])
			self.__auth[t[0]].set_access_token(t[3], t[4])
	def shell_loop(self):
		self.__current_user = None
		self.__prompt       = "> "
		try:
			while True:
				try:
					line = raw_input(self.__prompt)
					line = line.strip()
					self.eval(line)
				except EOFError:
					raise
				except KeyboardInterrupt:
					sys.stdout.write("\n")
				except Exception as e:
					print "type: %s"    % type(e)
					print "args: %s"    % e.args
					print "message: %s" % e.message
					print "e: %s"       % e
		except EOFError:
			sys.stdout.write("\n")
	def new_auth(self):
		pair = []
		if self.__auth:
			sys.stdout.write("Please select screen_name which you want to use same consumer as (or EMPTY, new one) > ")
			line = sys.stdin.readline().strip()
			if line:
				if line not in self.__auth:
					sys.stdout.write("You do NOT have @%s in auth dict.\n" % line)
					return
				pair.append(self.__auth[line]._consumer.key)
				pair.append(self.__auth[line]._consumer.secret)
		if not pair:
			sys.stdout.write("Consumer Key   : ")
			pair.append(sys.stdin.readline().rstrip())
			sys.stdout.write("Consumer Secret: ")
			pair.append(sys.stdin.readline().rstrip())
		auth = tweepy.OAuthHandler(*pair)
		sys.stdout.write("Please access: %s\n" % auth.get_authorization_url())
		sys.stdout.write("Input PIN: ")
		auth.get_access_token(sys.stdin.readline().strip())
		self.__auth[auth.get_username()] = auth
		fp = open(self.__authfile, "r")
		org = filter(lambda l: len(re.compile("^(.*?)(//.*)?$").search(l.strip()).group(0).rstrip().split()) != 5,
		             fp)
		fp.close()
		fp = open(self.__authfile, "w")
		pprint.pprint(org)
		fp.truncate(0)
		fp.writelines(org + ["%s %s %s %s %s\n" % (k, v._consumer.key, v._consumer.secret, v.access_token.key, v.access_token.secret) for k, v in self.__auth.items()])
	def eval(self, *commands):
		for command in commands:
			None

if __name__ == "__main__":
	authfile = DEFAULT_AUTHFILE
	if "-f" in sys.argv:
		idx = sys.argv.index("-f") + 1
		if idx == len(sys.argv, 1):
			sys.exit("-f option needs FILE NAME")
		authfile = sys.argv[idx]
	sh = TweetShell(authfile)
	sh.shell_loop()
