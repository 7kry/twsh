import __init__
import sys

authfile = __init__.DEFAULT_AUTHFILE
if "-f" in sys.argv:
	idx = sys.argv.index("-f") + 1
	if idx == len(sys.argv, 1):
		sys.exit("-f option needs FILE NAME")
	authfile = sys.argv[idx]
sh = __init__.TweetShell(authfile)
sh.shell_loop()
