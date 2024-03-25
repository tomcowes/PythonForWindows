import sys
import os.path
import pprint
sys.path.append(os.path.abspath(__file__ + "\..\.."))

import pfw_windows
import pfw_windows.test
import pfw_windows.debug

from pfw_windows.generated_def.winstructs import *



class MyDebugger(pfw_windows.debug.Debugger):
    def on_exception(self, exception):
        code = exception.ExceptionRecord.ExceptionCode
        addr = exception.ExceptionRecord.ExceptionAddress
        print("Got exception {0} at 0x{1:x}".format(code, addr))


class PrintUnicodeString(pfw_windows.debug.Breakpoint):
    def __init__(self, addr, argument_position):
        super(PrintUnicodeString, self).__init__(addr)
        self.arg_pos = argument_position


    def trigger(self, dbg, exc):
        p = dbg.current_process
        t = dbg.current_thread
        esp = t.context.Esp

        unicode_string_addr = p.read_ptr(esp + (self.arg_pos + 1) * 4)
        wstring_addr = p.read_ptr(unicode_string_addr + 4)
        dll_loaded = p.read_wstring(wstring_addr).lower()
        print("Loading <{0}>".format(dll_loaded))

        if dll_loaded.endswith("comctl32.dll"):
            print("Ask to load <comctl32.dll>: exiting process")
            dbg.current_process.exit()


calc = pfw_windows.test.pop_proc_32(dwCreationFlags=DEBUG_PROCESS)
d = MyDebugger(calc)
d.add_bp(PrintUnicodeString("ntdll!LdrLoadDll", argument_position=2))
d.loop()

