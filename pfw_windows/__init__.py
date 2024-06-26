"""
Python for Windows
A lot of python object to help navigate windows stuff

Exported:

    system : :class:`pfw_windows.winobject.System`

    current_process : :class:`pfw_windows.winobject.CurrentProcess`

    current_thread : :class:`pfw_windows.winobject.CurrentThread`
"""

# check we are on windows
import sys
if sys.platform != "win32":
    raise NotImplementedError("It's called PythonForWindows not PythonFor{0}".format(sys.platform.capitalize()))

import warnings
warnings.filterwarnings('once', category=DeprecationWarning, module=__name__)

from pfw_windows import winproxy
from pfw_windows import winobject

from .winobject.system import System
from .winobject.process import CurrentProcess, CurrentThread, WinProcess, WinThread
from .winobject.file import WinFile


system = System()
current_process = CurrentProcess()
current_thread = CurrentThread()

del System
del CurrentProcess
del CurrentThread

# Late import: other imports should go here
# Do not move it: risk of circular import

import pfw_windows.utils
import pfw_windows.wintrust
import pfw_windows.syswow64
import pfw_windows.com

__all__ = ["system", 'current_process', 'current_thread']
