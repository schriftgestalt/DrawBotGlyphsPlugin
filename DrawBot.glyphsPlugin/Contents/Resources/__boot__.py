
def _run(script):
	global __file__
	import os, sys
	sys.frozen = 'macosx_plugin'
	base = os.environ['RESOURCEPATH']
	path = os.path.join(base, script)
	__file__ = path
	execfile(path, globals(), globals())

_run('DrawBotDocument.py')
