#! /usr/bin/env python2

import sys
import os
import re
import tweepy
import readline

DEFAULT_AUTHFILE = os.path.expanduser("~") + "/.twitter_auth"

class TweetShell:
	def __init__(self, authfile):
		a = map(lambda l: re.compile("^(.*?)(//.*)?$").search(l.strip()).group(0).rstrip().split(),
		        open(authfile))
		a = filter(lambda l: len(l) == 5, a)
		self.__auth = {}
		for t in a:
			if t[0] in self.__auth:
				sys.exit("Duplicated screen_name in the authfile.")
			self.__auth[t[0]] = tweepy.OAuthHandler(t[1], t[2])
			self.__auth[t[0]].set_access_token(t[3], t[4])
	def new_auth():
		try:
			pair = []
			if self.__auth:
				sys.stdout.write("Please select screen_name which you want to use same consumer as (or EMPTY, new one) > ")
				line = sys.stdin.readline().strip()
				if line:
					if line not in self.__auth:
						sys.stdout("You do NOT have %s in auth dict." % line)
						return
					pair.append(self.__auth[line]._consumer.key)
					pair.append(self.__auth[line]._consumer.secret)
			if not pair:
				sys.stdout.write("Consumer Key   : ")
				pair.append(sys.stdin.readline().rstrip())
				sys.stdout.write("Consumer Secret: ")
				pair.append(sys.stdin.readline().rstrip())
			auth = tweepy.OAuthHandler(*pair)
			sys.stdout.writelines("Please access: %s" % auth.get_authorization_url())
			sys.stdout.write("Input PIN: ")
			auth.get_access_token(sys.stdin.readline().strip())
			# TODO: Reflesh auth and authfile
		except Exception as e:
			sys.stdout.writelines(
					"Some unexpected error occured: %s" % type(e),
					"    %s" % e.args,
					"    %s" % e.message)

if __name__ == "__main__":
	authfile = DEFAULT_AUTHFILE
	if "-f" in sys.argv:
		idx = sys.argv.index("-f") + 1
		if idx == len(sys.argv, 1):
			sys.exit("-f option needs FILE NAME")
		authfile = sys.argv[idx]
	sh = TweetShell(authfile)
