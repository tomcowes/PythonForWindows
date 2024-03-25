import argparse
import os

import pfw_windows
import pfw_windows.debug
import pfw_windows.test


parser = argparse.ArgumentParser(prog=__file__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--dbghelp', help='The path of DBG help to use (default use env:PFW_DBGHELP_PATH)')
args = parser.parse_args()
print(args)

if args.dbghelp:
    symbols.set_dbghelp_path(args.dbghelp)
else:
    if "PFW_DBGHELP_PATH" not in os.environ:
        print("Not dbghelp path given and no environ var 'PFW_DBGHELP_PATH' sample may fail")


class MyInfoBP(pfw_windows.debug.Breakpoint):
    COUNT = 0
    def trigger(self, dbg, exc):
        cursym = dbg.current_resolver[exc.ExceptionRecord.ExceptionAddress]
        print("Breakpoint triggered at: {0}".format(cursym))
        print(repr(cursym))
        MyInfoBP.COUNT += 1
        if MyInfoBP.COUNT == 4:
            print("Quitting")
            dbg.current_process.exit()
        print("")

dbg = pfw_windows.debug.SymbolDebugger.debug(b"c:\\windows\\system32\\notepad.exe")
dbg.add_bp(MyInfoBP("kernelbase!CreateFileInternal+2"))
dbg.add_bp(MyInfoBP("ntdll!LdrpInitializeProcess"))
dbg.loop()