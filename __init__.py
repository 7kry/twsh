#! /usr/bin/env python3

import sys
import cmd
import os.path
import yaml
import tweepy
import subprocess
import tempfile
import re

class TweetShell(cmd.Cmd):
  prompt = '(nologin)> '
  __consumer_key = 'IoapgGY0Of2AT84itoGw'
  __consumer_sec = 'edB8pOHB9XSN0waHg8fiHWCGfb5Cur8LbF7yEzXpE'
  __current_auth = None
  __api = None
  __timeline_count = 200

  def __init__(self, authfile = os.path.expanduser('~/.twshell_auth')):
    cmd.Cmd.__init__(self)
    self.__authfile = authfile
    self.__load_authfile()

  def __login(self, account):
    self.__auth = tweepy.OAuthHandler(account['consumer_key'], account['consumer_secret'])
    self.__auth.set_access_token(account['token'], account['token_secret'])
    self.__api = tweepy.API(self.__auth)

  def __load_authfile(self):
    if os.path.exists(self.__authfile):
      with open(self.__authfile) as fp:
        self.__auth = yaml.load(fp)
    else:
      self.__auth = {}
      with open(self.__authfile, 'w') as fp:
        yaml.dump(self.__auth, fp)

  def __resolve_entities(org, entities):
    urls = dict(map(lambda elem: (elem['url'], elem['expanded_url']), entities['urls']))
    return re.sub(
              r'https?://t\.co/[a-z0-9]+',
              lambda tco: urls.get(tco.group(0), tco.group(0)),
              org,
              flags = re.I | re.M)

  def __stringify_status(status):
    header = '@%s (%s)' % (status.author.screen_name, status.author.name)
    text = status.text
    entities = status.entities
    date = status.created_at
    source = status.source
    if 'retweeted_status' in status.__dict__:
      rstatus = status.retweeted_status
      header += ' retweets @%s (%s)' % (rstatus.author.screen_name, rstatus.author.name)
      text = rstatus.text
      entities = rstatus.entities
      date = rstatus.created_at
      source = '%s (retweeted by %s)' % (rstatus.source, source)

    return '''\
{header}
{text}
{date} via {source}'''.format(
      header = header,
      text = TweetShell.__resolve_entities(text, entities),
      date = date,
      source = source,
    )

  def do_home(self, arg):
    print("\n\n".join(map(TweetShell.__stringify_status, reversed(self.__api.home_timeline(count = self.__timeline_count)))))

  def do_mentions(self, arg):
    print("\n\n".join(map(TweetShell.__stringify_status, reversed(self.__api.mentions_timeline(count = self.__timeline_count)))))

  def do_login(self, identifier):
    self.__login(self.__auth[identifier])
    self.prompt = '%s> ' % identifier

  def do_update(self, arg):
    text = None
    with tempfile.NamedTemporaryFile(prefix = 'twshell-') as fp:
      subprocess.call(' '.join([os.getenv('EDITOR', 'vi'), fp.name]), shell = True)
      fp.seek(0)
      text = fp.read().strip()
    if not text:
      print('Interrupted because text is empty...')
      return
    print(TweetShell.__stringify_status(self.__api.update_status(text)))

  def do_EOF(self, *argv):
    sys.exit(0)
