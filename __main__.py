import __init__
from __init__ import *

authfile = __init__.DEFAULT_AUTHFILE
if "-a" in sys.argv:
	idx = sys.argv.index("-a") + 1
	if idx == len(sys.argv, 1):
		sys.exit("-f option needs FILE NAME")
	authfile = sys.argv[idx]
sh = __init__.TweetShell(authfile)
if "-e" in sys.argv:
	lines = map(lambda idx: sys.argv[idx], filter(lambda idx : sys.argv[idx - 1] == "-e", range(2, len(sys.argv))))
	sh.eval(*lines)
else:
	rcfile = os.path.expanduser("~") + "/.twshellrc"
	if os.path.exists(rcfile):
		for line in open(rcfile):
			sh.eval(line)
	sh.shell_loop()
