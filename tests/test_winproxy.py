import pytest

import pfw_windows
import pfw_windows.generated_def as gdef

from .pfwtest import *

pytestmark = pytest.mark.usefixtures('check_for_gc_garbage')


def test_createfileA_fail():
    with pytest.raises(WindowsError) as ar:
        pfw_windows.winproxy.CreateFileA(b"NONEXISTFILE.FILE")


def test_lstrcmpa():
    assert pfw_windows.winproxy.lstrcmpA(b"LOL", b"NO-LOL")
    assert not pfw_windows.winproxy.lstrcmpA(b"LOL", b"LOL")

def test_getsystemmetrics():
    """Test nothing is raised when GetSystemMetrics() returns 0"""
    # Using a suit of value that may return 0
    pfw_windows.winproxy.GetSystemMetrics(gdef.SM_DIGITIZER)
    pfw_windows.winproxy.GetSystemMetrics(gdef.SM_CLEANBOOT)
    pfw_windows.winproxy.GetSystemMetrics(gdef.SM_MOUSEHORIZONTALWHEELPRESENT)
    pfw_windows.winproxy.GetSystemMetrics(gdef.SM_SERVERR2)
    pfw_windows.winproxy.GetSystemMetrics(gdef.SM_SLOWMACHINE)
    pfw_windows.winproxy.GetSystemMetrics(gdef.SM_SWAPBUTTON)
    pfw_windows.winproxy.GetSystemMetrics(gdef.SM_TABLETPC)


def test_NtStatusException_winerror():
    assert gdef.NtStatusException(2).winerror == 2
    assert gdef.NtStatusException(1234).winerror == 1234

def test_resolve():
    ntdll = pfw_windows.current_process.peb.modules[1]
    assert ntdll.name == "ntdll.dll"
    assert ntdll.pe.exports["NtCreateFile"] == pfw_windows.winproxy.resolve(pfw_windows.winproxy.NtCreateFile)

