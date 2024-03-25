import sys
import os.path
import pprint
sys.path.append(os.path.abspath(__file__ + "\..\.."))

import pfw_windows
import pfw_windows.test
import pfw_windows.debug

from pfw_windows.generated_def.winstructs import *

# Just a debugger that follow NtCreateFile and print filename & handler
from debug_functionbp import FollowNtCreateFile


def follow_create_file(pid):
    print("Finding process with pid <{0}>".format(pid))
    target = [p for p in pfw_windows.system.processes if p.pid == pid][0]
    print("Target is {0}".format(target))
    dbg = pfw_windows.debug.Debugger.attach(target)
    print("Debugger attached: {0}".format(dbg))
    print("")
    dbg.add_bp(FollowNtCreateFile())
    dbg.loop()

if __name__ == "__main__":
    # Create a non-debugged process safe to debug
    calc = pfw_windows.test.pop_proc_32(dwCreationFlags=0)
    # Give ovnly the PID to follow_create_file
    follow_create_file(calc.pid)
