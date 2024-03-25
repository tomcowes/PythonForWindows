import sys
import os.path
import pprint
sys.path.append(os.path.abspath(__file__ + "\..\.."))

import ctypes
import pfw_windows
import pfw_windows.test

from pfw_windows.generated_def.winstructs import *

remote_code = """
import pfw_windows
from pfw_windows.generated_def.winstructs import *

pfw_windows.utils.create_console()

class YOLOHXBP(pfw_windows.debug.HXBreakpoint):
    def trigger(self, dbg, exc):
        p = pfw_windows.current_process
        arg_pos = 2
        context = dbg.get_exception_context()
        esp = context.Esp
        unicode_string_addr = p.read_ptr(esp + (arg_pos + 1) * 4)
        wstring_addr = p.read_ptr(unicode_string_addr + 4)
        dll_loaded = p.read_wstring(wstring_addr)
        print("I AM LOADING <{0}>".format(dll_loaded))

d = pfw_windows.debug.LocalDebugger()

exp = pfw_windows.current_process.peb.modules[1].pe.exports
#pfw_windows.utils.FixedInteractiveConsole(locals()).interact()
ldr = exp["LdrLoadDll"]
d.add_bp(YOLOHXBP(ldr))

"""

c = pfw_windows.test.pop_proc_32(dwCreationFlags=CREATE_SUSPENDED)
c.execute_python(remote_code)
c.threads[0].resume()

import time
time.sleep(2)
c.exit()