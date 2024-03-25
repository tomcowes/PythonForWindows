import ctypes
import pytest
import pfw_windows

from .pfwtest import *

@check_for_gc_garbage
class TestSystemWithCheckGarbage(object):
    def test_version(self):
        return pfw_windows.system.version

    def test_version_name(self):
        return pfw_windows.system.version_name

    def test_version_product_type(self):
        return pfw_windows.system.product_type

    def test_version_edition(self):
        return pfw_windows.system.edition

    def test_version_windir(self):
        return pfw_windows.system.windir


    def test_computer_name(self):
        computer_name = pfw_windows.system.computer_name
        assert computer_name
        assert isinstance(computer_name, str)

    def test_services(self):
        return pfw_windows.system.services

    def test_logicaldrives(self):
        return pfw_windows.system.logicaldrives

    def test_wmi(self):
        return pfw_windows.system.wmi

    def test_handles(self):
        return pfw_windows.system.handles

    def test_bitness(self):
        return pfw_windows.system.bitness

    def test_evtlog(self):
        return pfw_windows.system.event_log

    def test_task_scheduler(self):
        return pfw_windows.system.task_scheduler

    def test_task_object_manager(self):
        return pfw_windows.system.object_manager

    def test_system_modules_ntosk(self):
        assert pfw_windows.system.modules[0].name.endswith(b"ntoskrnl.exe")


@check_for_gc_garbage
class TestSystemWithCheckGarbageAndHandleLeak(object):
    def test_threads(self):
        return pfw_windows.system.threads

    def test_processes(self):
        procs = pfw_windows.system.processes
        assert pfw_windows.current_process.pid in [p.pid for p in procs]

    def test_system_modules(self):
        return pfw_windows.system.modules


# Test environement dict
# On py3 this will just test os.environ, but at least we can expect some consistence

UNICODE_STRING_1 = u"\u4e2d\u56fd\u94f6\u884c\u7f51\u94f6\u52a9\u624b" # some chinese
UNICODE_RU_STRING = u"\u0441\u0443\u043a\u0430\u0020\u0431\u043b\u044f\u0442\u044c" # CYKA BLYAT in Cyrillic
UNICODE_UNICORD = u'\U0001f984' # Encoded on 4 char in utf-16
UNICODE_LOIC_ESCAPE = u'lo\xefc' # Loic with trema

def check_env_variable_exist(name):
    buf = ctypes.create_unicode_buffer(0x1000)
    try:
        pfw_windows.winproxy.GetEnvironmentVariableW(name, buf, 0x1000)
    except WindowsError as e:
        if e.winerror == gdef.ERROR_ENVVAR_NOT_FOUND:
            return False
        raise
    return True

def test_unicode_environ_dict():
    unicode_environ = pfw_windows.system.environ

    unicode_environ["lower"] = "lower"
    unicode_environ[UNICODE_LOIC_ESCAPE] = UNICODE_UNICORD

    assert "LOWER" in unicode_environ
    assert "LOwer" in unicode_environ # Case does not count on __contains__

    assert UNICODE_LOIC_ESCAPE in unicode_environ
    assert unicode_environ[UNICODE_LOIC_ESCAPE] == UNICODE_UNICORD

    assert check_env_variable_exist("lower")
    del unicode_environ["Lower"]
    assert not check_env_variable_exist("lower")

    assert check_env_variable_exist(UNICODE_LOIC_ESCAPE)
    del unicode_environ[UNICODE_LOIC_ESCAPE]
    assert not check_env_variable_exist(UNICODE_LOIC_ESCAPE)

    assert not check_env_variable_exist(UNICODE_STRING_1)
    unicode_environ[UNICODE_STRING_1] = UNICODE_RU_STRING
    assert check_env_variable_exist(UNICODE_STRING_1)

