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
  __alph_id = {}
  __id_alph = {}
  __alph = 0
  __statuses = {}

  def __init__(self, authfile = os.path.expanduser('~/.twshell_auth')):
    cmd.Cmd.__init__(self)
    self.__authfile = authfile
    self.__load_authfile()

  def __login(self, account):
    self.__current_auth = tweepy.OAuthHandler(account['consumer_key'], account['consumer_secret'])
    self.__current_auth.set_access_token(account['token'], account['token_secret'])
    self.__api = tweepy.API(self.__current_auth)

  def __load_authfile(self):
    if os.path.exists(self.__authfile):
      with open(self.__authfile) as fp:
        self.__auth = yaml.load(fp)
    else:
      self.__auth = {}
      with open(self.__authfile, 'w') as fp:
        yaml.dump(self.__auth, fp)

  def __twentysix_generator(num):
    while True:
      yield num % 26
      num //= 26
      if num <= 0:
        break

  def __alloc_alph(self, id):
    if id in self.__id_alph:
      return self.__id_alph[id]
    ret = ''.join(map(lambda fig: chr(ord('a') + fig), reversed(list(TweetShell.__twentysix_generator(self.__alph)))))
    self.__alph += 1
    self.__id_alph[id] = ret
    self.__alph_id[ret] = id
    return ret

  def __resolve_entities(org, entities):
    urls = dict(map(lambda elem: (elem['url'], elem['expanded_url']), entities.get('urls', []) + entities.get('media', [])))
    return re.sub(
              r'https?://t\.co/[a-z0-9]+',
              lambda tco: urls.get(tco.group(0), tco.group(0)),
              org,
              flags = re.I | re.M)

  def __store_status(self, status):
    self.__statuses[status.id] = status
    self.__alloc_alph(status.id)
    return status

  def __stringify_status(self, status):
    alph = self.__alloc_alph(status.id)
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
[{alph}] {header}
{text}
{date} via {source}'''.format(
      alph = alph,
      header = header,
      text = TweetShell.__resolve_entities(text, entities),
      date = date,
      source = source,
    )

  def emptyline(self):
    None

  def __do_timeline(self, tlfunc):
    timeline = tlfunc(count = self.__timeline_count)
    for elem in timeline:
      self.__store_status(elem)
    print("\n\n".join(map(self.__stringify_status, reversed(timeline))))

  def do_home(self, arg):
    return self.__do_timeline(self.__api.home_timeline)

  def do_mentions(self, arg):
    return self.__do_timeline(self.__api.mentions_timeline)

  def __parse_userarg(arg):
    argdict = {}
    if arg.startswith('@'):
      argdict['screen_name'] = arg[1:]
    elif re.match('^\d+$', arg):
      argdict['id'] = int(arg)
    else:
      argdict['screen_name'] = arg
    return argdict

  def do_user(self, arg):
    argdict = TweetShell.__parse_userarg(arg)
    return self.__do_timeline(lambda count: self.__api.user_timeline(count = count, **argdict))

  def do_list(self, arg):
    argdict = {}
    m = re.match('^@?(.*?)/(.+)', arg)
    if m:
      if m.group(1):
        argdict['owner_screen_name'] = m.group(1)
      argdict['slug'] = m.group(2)
    elif re.match('^\d+$', arg):
      argdict['list_id'] = int(arg)
    else:
      argdict['slug'] = arg
    return self.__do_timeline(lambda count: self.__api.list_timeline(count = count, **argdict))

  def do_lslists(self, arg):
    argdict = TweetShell.__parse_userarg(arg)
    if 'id' in argdict:
      argdict['user_id'] = argdict['id']
      del argdict['id']
    ls = self.__api.lists_all(**argdict)
    for elem in ls:
      print('{full_name} {id} {description}'.format(
          full_name = elem.full_name,
          id = elem.id,
          description = elem.description))

  def do_login(self, identifier):
    self.__login(self.__auth[identifier])
    self.prompt = '%s> ' % identifier

  def __seek_alph(self, alph):
    return self.__alph_id[alph]

  def do_update(self, arg):
    text = None
    in_reply_to_status_id = None
    with tempfile.NamedTemporaryFile(prefix = 'twshell-') as fp:
      if arg:
        in_reply_to_status_id = self.__seek_alph(arg)
        fp.write(('@' + self.__statuses[in_reply_to_status_id].author.screen_name + ' ').encode('ascii'))
        fp.flush()
      subprocess.call(' '.join([os.getenv('EDITOR', 'vi'), fp.name]), shell = True)
      fp.seek(0)
      text = fp.read().strip()
      if not text:
        print('Interrupted because text is empty...')
        return
      print(self.__stringify_status(self.__api.update_status(text, in_reply_to_status_id = in_reply_to_status_id)))

  def do_EOF(self, *argv):
    sys.exit(0)
