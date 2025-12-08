import shlex
import subprocess
import threading

from django.conf import settings


class Shared(object):
    pass


def _target(obj, cmd):
    obj.stars_process = subprocess.Popen(cmd)
    obj.stars_process.communicate()


def activate(winpath):
    commandline = shlex.split(
        r'wine C:\\stars\\stars!.exe'
        r' -a {winpath}game.def'.format(winpath=winpath)
    )
    execute(commandline)


def generate(winpath):
    commandline = shlex.split(
        r'wine C:\\stars\\stars\!.exe'
        r' -g {winpath}game.hst'.format(winpath=winpath)
    )
    execute(commandline)


def execute(commandline):
    obj = Shared()
    thread = threading.Thread(target=_target, args=(obj, commandline))
    thread.start()

    thread.join(getattr(settings, 'STARSWEB_TIMEOUT', 5 * 60))
    if thread.is_alive():
        obj.stars_process.terminate()
        thread.join()
        raise Exception("Stars! timed out.")
