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
import subprocess
import xml.sax.saxutils

DEFAULT_AUTHFILE = os.path.expanduser("~") + "/.twitter_auth"

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
		self.__commands = {
				"new_auth"    : self.__new_auth,
				"login"       : self.__login,
				"whoami"      : lambda *argv: pprint.pprint(tweepy.API(self.__current_user).me().__dict__),
				"whois"       : lambda *argv: pprint.pprint(tweepy.API(self.__current_user).get_user(screen_name = argv[0]).__dict__),
				"update_stdin": lambda *argv: self.__update(sys.stdin.read(), *argv),
				"update"      : lambda *argv: self.__update_with_editor(*argv),
				"update_photo": lambda *argv: self.__update_with_photo(*argv),
				"favor"       : lambda *argv: pprint.pprint(tweepy.API(self.__current_user).create_favorite(*map(lambda x: int(x), argv)).__dict__),
				"unfavor"     : lambda *argv: pprint.pprint(tweepy.API(self.__current_user).destroy_favorite(*map(lambda x: int(x), argv)).__dict__),
				"retweet"     : lambda *argv: pprint.pprint(tweepy.API(self.__current_user).retweet(*map(lambda x: int(x), argv)).__dict__),
				"follow_id"   : lambda *argv: pprint.pprint(tweepy.API(self.__current_user).create_friendship(*map(lambda x: int(x), argv)).__dict__),
				"follow_sn"   : lambda *argv: pprint.pprint(tweepy.API(self.__current_user).create_friendship(*argv).__dict__),
				"unfollow_id"   : lambda *argv: pprint.pprint(tweepy.API(self.__current_user).destroy_friendship(*map(lambda x: int(x), argv)).__dict__),
				"unfollow_sn"   : lambda *argv: pprint.pprint(tweepy.API(self.__current_user).destroy_friendship(*argv).__dict__),
				"profile_id"  : lambda *argv: pprint.pprint(tweepy.API(self.__current_user).get_user(*map(lambda x: int(x), argv)).__dict__),
				"profile_sn"  : lambda *argv: pprint.pprint(tweepy.API(self.__current_user).get_user(*argv).__dict__),
				"user_sn"     : lambda sn:    sys.stdout.write("\n".join(map(self.__tl_stringify, reversed(tweepy.API(self.__current_user).user_timeline(count=200, screen_name=sn))))),
				"user_id"     : lambda uid:    sys.stdout.write("\n".join(map(self.__tl_stringify, reversed(tweepy.API(self.__current_user).user_timeline(count=200, id=uid))))),
				"home"        : lambda *argv: self.__timeline(u"home_timeline", *argv),
				"mentions"    : lambda *argv: self.__timeline(u"mentions_timeline", *argv),
				"favorites"   : lambda *argv: self.__timeline(u"favorites", *argv),
				"destroy"     : lambda *argv: pprint.pprint(tweepy.API(self.__current_user).destroy_status(*map(lambda x: int(x), argv)).__dict__),
				"shell"       : lambda *argv: subprocess.call(argv),
				"help"        : lambda *args: sys.stdout.writelines(sorted(map(lambda e: e + "\n", self.__commands.keys()))),
			}
		#Synonims
		self.__commands["?"]  = self.__commands["help"]
		# States & Settings
		self.__current_user   = None
		self.__prompt         = "> "
		self.__sn             = ""
		self.__tl_format      = u"""\
@{screen_name} {id} :
{status}
{date} via {source}
"""
		self.__tl_rted_format = u"""\
@{screen_name} (RTed by @{rter_screen_name}) {id} :
{status}
{date} via {source}
"""
	def shell_loop(self):
		try:
			while True:
				try:
					line = raw_input(self.__prompt if sys.stdin.isatty() else "")
					line = line.strip()
					self.eval(line)
				except EOFError:
					raise
				except KeyboardInterrupt:
					sys.stdout.write("KeyboardInterrupt\n")
				except:
					sys.stdout.write(traceback.format_exc(sys.exc_info()[2]))
		except EOFError:
			sys.stdout.write("\n")
	def __update(self, text, *argv):
		_argv = []
		l     = len(argv)
		if l >= 1:
			_argv.append(int(argv[0]))
		sys.stdout.write(self.__tl_stringify(tweepy.API(self.__current_user).update_status(text, *_argv)))
	def __update_with_photo(self, *argv):
		_argv = []
		tmp = tempfile.mktemp(prefix = 'twshell-%s-' % self.__sn)
		edt = os.getenv("EDITOR", "vi")
		subprocess.call([edt, tmp])
		if not os.path.exists(tmp):
			sys.stdout.write("Interrupt\n")
			return
		fp = open(tmp)
		sys.stdout.write(self.__tl_stringify(
			tweepy.API(self.__current_user).update_with_media(argv[0], status = fp.read().rstrip(), in_reply_to_status_id = int(argv[1]))\
				if len(argv) >= 2 else\
				tweepy.API(self.__current_user).update_with_media(argv[0], status = fp.read().rstrip())))
		fp.close()
		os.remove(tmp)
	def __update_with_editor(self, *argv):
		tmp = tempfile.mktemp(prefix = 'twshell-%s-' % self.__sn)
		edt = os.getenv("EDITOR", "vi")
		while True:
			subprocess.call([edt, tmp])
			if not os.path.exists(tmp):
				sys.stdout.write("Interrupt\n")
				return
			fp = open(tmp)
			txt = fp.read()
			print(txt)
			sys.stdout.write("OK? ([y]es/[c]ancel/or else to re-edit)> ")
			answer = sys.stdin.readline().strip()
			if answer == "y":
				self.__update(txt, *argv)
				break
			if answer == "c":
				break
		fp.close()
		os.remove(tmp)
	def __new_auth(self, *arv):
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
		org = filter(lambda l: len(re.compile("^(.*?)(//.*)?$").search(l.strip()).group(0).rstrip().split()) != 5, fp)
		fp.close()
		fp = open(self.__authfile, "w")
		fp.writelines(org + ["%s %s %s %s %s\n" % (k, v._consumer.key, v._consumer.secret, v.access_token.key, v.access_token.secret) for k, v in self.__auth.items()])
	def __login(self, *argv):
		term = open(os.ctermid(), "r+w")
		if argv:
			sn = argv[0]
		else:
			for sn in self.__auth.keys():
				term.write("* @%s\n" % sn)
			term.write("WHICH?> ")
			sn = term.readline().strip()
		if sn not in self.__auth.keys():
			term.write("%s was NOT found.\n" % sn)
			return
		self.__current_user = self.__auth[sn]
		self.__prompt = "%s> " % sn
		self.__sn     = sn
	def __tl_stringify(self, status):
		if u"retweeted_status" in status.__dict__:
			return self.__tl_rted_format.format(
					screen_name      = status.retweeted_status.author.screen_name,
					rter_screen_name = status.author.screen_name,
					id               = status.id,
					status           = xml.sax.saxutils.unescape(status.retweeted_status.text),
					date             = u"%s" % status.retweeted_status.created_at,
					source           = status.retweeted_status.source,
				)
		else:
			return self.__tl_format.format(
					screen_name = status.author.screen_name,
					id          = status.id,
					status      = xml.sax.saxutils.unescape(status.text),
					date        = u"%s" % status.created_at,
					source      = status.source,
				)
	def __timeline(self, tl_type, *argv):
		sys.stdout.write("\n".join(map(self.__tl_stringify, reversed(tweepy.API.__dict__[tl_type](tweepy.API(self.__current_user), count=200, *argv)))))
	def eval(self, *commands):
		for command in map(lambda l: l.strip(), commands):
			m = map(lambda e: e.group("quoted").replace("''", "'") if e.group("quoted") else e.group("literal"),
				re.compile("(?:'(?P<quoted>(?:''|[^'])*)'|(?P<literal>\S+))").finditer(command))
			if not m:
				return
			if (m[0] not in self.__commands):
				sys.stdout.write("Command not found.\n")
				return
			self.__commands[m[0]](*m[1:len(m)])
	@classmethod
	def ask_yn(c, messace = ""):
		fp = open(os.ctermid(), "r+w")
		fp.write("y/n> ")
		return True if fp.readline().rstrip().lower() == "y" else False
