#! /usr/bin/env python2
# vim:fileencoding=UTF-8

import sys
import os
import re
import tweepy
import readline
import pprint
import traceback
import tempfile

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
		self.commands = {
				"new_auth": self.new_auth,
				"login"   : self.login,
				"whoami"  : self.whoami,
				"tweet"   : self.tweet,
			}
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
				except:
					sys.stdout.write(traceback.format_exc(sys.exc_info()[2]))
		except EOFError:
			sys.stdout.write("\n")
	def tweet(self, text, *others):
		pprint.pprint(tweepy.API(self.__current_user).update_status(text, *others).__dict__)
	def new_auth(self, *arv):
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
		fp.writelines(org + ["%s %s %s %s %s\n" % (k, v._consumer.key, v._consumer.secret, v.access_token.key, v.access_token.secret) for k, v in self.__auth.items()])
	def login(self, *argv):
		term = open("/dev/tty", "r+w")
		for sn in self.__auth.keys():
			term.write("  @%s\n" % sn)
		term.write("WHICH?> ")
		sn = term.readline().strip()
		if sn not in self.__auth.keys():
			term.write("NOT FOUND.\n")
		self.__current_user = self.__auth[sn]
		self.__prompt = "%s> " % sn
	def whoami(self, *argv):
		pprint.pprint(tweepy.API(self.__current_user).me().__dict__)
	def eval(self, *commands):
		for command in map(lambda l: l.strip(), commands):
			m = re.compile('\S+').findall(command)
			if not m:
				return
			if m[0] not in self.commands:
				sys.stdout.write("Command not found.")
				return
			self.commands[m[0]](*m[1:len(m)])

if __name__ == "__main__":
	authfile = DEFAULT_AUTHFILE
	if "-f" in sys.argv:
		idx = sys.argv.index("-f") + 1
		if idx == len(sys.argv, 1):
			sys.exit("-f option needs FILE NAME")
		authfile = sys.argv[idx]
	sh = TweetShell(authfile)
	sh.shell_loop()
