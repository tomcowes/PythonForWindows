import datetime

import pytest
from .pfwtest import *

import pfw_windows


testbasekeypath = r"HKEY_CURRENT_USER\SOFTWARE\PythonForWindows\Test"
basekeytest = pfw_windows.system.registry(testbasekeypath, gdef.KEY_WOW64_64KEY | gdef.KEY_ALL_ACCESS)

if not basekeytest.exists:
    basekeytest.create()

if pfw_windows.pycompat.is_py3:
    REG_TEST_BINARY_DATA = b"BIN_DATA\x01\x02\x03\x00" + bytes(range(256))
else:
    REG_TEST_BINARY_DATA = "BIN_DATA\x01\x02\x03\x00" + "".join(chr(i) for i in range(256))

@pytest.fixture()
def empty_test_base_key():
    assert basekeytest.exists
    # Depends on test_registry_key_empty :)
    basekeytest.empty()

# Clean registry before everytest
pytestmark = pytest.mark.usefixtures("empty_test_base_key")


@pytest.mark.parametrize("value", [1, "LOL", 0x11223344, ""])
def test_registry_set_get_simple_values(value):
    basekeytest["tst1"] = value
    assert basekeytest["tst1"].value == value


# TODO: test with other registry type (the stranges ones)
@pytest.mark.parametrize("value, type", [
    (0x11223344, gdef.REG_DWORD), # same as gdef.REG_DWORD_LITTLE_ENDIAN
    (0x11223344, gdef.REG_DWORD_BIG_ENDIAN),
    (0x1122334455667788, gdef.REG_QWORD), # same as gdef.REG_QWORD_LITTLE_ENDIAN
    ("", gdef.REG_SZ),
    ("Hello world", gdef.REG_SZ),
    ("Hello world %path%", gdef.REG_EXPAND_SZ),
    (["AAAA", "BBBB", "CCCC"], gdef.REG_MULTI_SZ),
    # Binary format and associated
    (REG_TEST_BINARY_DATA, gdef.REG_BINARY),
    (b"Hello-world", gdef.REG_LINK),
    (b"", gdef.REG_NONE),
    (b"Not really None :)\x11\x22\x00ABCD", gdef.REG_NONE),
    (b"Test-Unknown-format", 0x11223344), # Unknown registry type
    (b"Test-Unknown-format\x00\x01\xff\xfe Lol", 0xffffffff), # Unknown registry type
])
def test_registry_set_get_simple_values_with_types(value, type):
    basekeytest["tst2"] = (value, type)
    assert basekeytest["tst2"].value == value


@pytest.mark.parametrize("value, type", [
    # "\xff\xd8".decode("utf-16") -> UnicodeDecodeError
    (b"\xff\xd8", gdef.REG_MULTI_SZ),
    # Is NOT valid UTF-16 (len == 33)
    (b"Hello\x00World\x00This is not unicode\x00\x00", gdef.REG_MULTI_SZ),
    # Is valid UTF-16 (len == 40)
    # Should the decoding be completly different ?
    (b"Hello\x00World\x00This is not really unicode\x00\x00", gdef.REG_MULTI_SZ),
])
def test_registry_badly_encoded_values(value, type):
    # Bypass any encoding logic to setup bad key
    keyname = "bad_encoding"
    buffer = pfw_windows.utils.BUFFER(gdef.BYTE).from_buffer_copy(value)
    pfw_windows.winproxy.RegSetValueExW(basekeytest.phkey, keyname, 0, type, buffer, len(buffer))
    # Not the best decoded value
    # But should not crash
    assert basekeytest[keyname]



UNICODE_PATH_NAME = u'\u4e2d\u56fd\u94f6\u884c\u7f51\u94f6\u52a9\u624b'
UNICODE_RU_STRING = u"\u0441\u0443\u043a\u0430\u0020\u0431\u043b\u044f\u0442\u044c" # CYKA BLYAT in Cyrillic

# Could be done in test_registry_set_get_simple_values
# But was the cause a special bug / reimplem due to _winreg using ANSI functions
# So create a special test with a very identifiable name / bug cause

@pytest.mark.parametrize("unistr", [
    u'c:\\users\\hakril\\appdata\\local\\temp\\test_unicode_\u4e2d\u56fd\u94f6\u884c\u7f51\u94f6\u52a9\u624bdbqsm3',
    '\u52a9' * 126,
    UNICODE_PATH_NAME,
    UNICODE_RU_STRING,
    u""
])
def test_registry_unicode_string_value(unistr):
    basekeytest["tst3"] = unistr
    assert basekeytest["tst3"].value == unistr

@pytest.mark.parametrize("unistr", [
    # Looks like this value with this size MAY lead to non-existing NULL BYTE ?
    # This bug is tested in test_registry_Reg2Py_SZ
    u'c:\\users\\hakril\\appdata\\local\\temp\\test_unicode_\u4e2d\u56fd\u94f6\u884c\u7f51\u94f6\u52a9\u624bdbqsm3',
    u'\u52a9' * 126,
    UNICODE_PATH_NAME,
    UNICODE_PATH_NAME * 10,
    UNICODE_RU_STRING * 10,
    UNICODE_RU_STRING
])
def test_registry_unicode_string_values_enumeration(unistr):
    basekeytest["tst5"] = unistr
    values_by_name = {x.name: x for x in basekeytest.values}
    assert values_by_name["tst5"].value == unistr


def test_registry_unicode_multi_string():
    TST_MULTI = [UNICODE_PATH_NAME, "Hello World", UNICODE_RU_STRING]
    basekeytest["tst4"] = (TST_MULTI, gdef.REG_MULTI_SZ)
    assert basekeytest["tst4"].value == TST_MULTI


@pytest.mark.parametrize("unistr", [UNICODE_PATH_NAME, UNICODE_RU_STRING])
def test_registry_unicode_value_name(unistr):
    basekeytest[unistr] = 42
    assert basekeytest[unistr].value == 42
    # assert unistr in [v.name for v in basekeytest.values]
    del basekeytest[unistr]

def test_registry_subkeys_create_delete():
    subname = "MyTestSubKey"
    subkey = basekeytest(subname)
    assert not subkey.exists
    subkey.create()
    assert subkey.exists
    subkey.delete()
    assert not subkey.exists

def test_registry_get_key_info():
    subname = "MyTestSubKeySizeInfo"
    subkey = basekeytest(subname).create()
    subkey["A"] = "12345"
    subkey["AAAA"] = "1"
    max_name_size, max_value_size = subkey.get_key_size_info()
    assert max_name_size == 4 # AAAA
    assert max_value_size == 6 * 2 # 12345\x00 -> 2 BYTE per char (utf-16)
    other_info = subkey.info
    assert other_info[0] == 0 # Nb subkeys
    assert other_info[1] == 2 # Nb values
    assert isinstance(other_info[2], pfw_windows.pycompat.int_types) # Last write

def test_registry_key_empty():
    subname = "MyTestKeyEmpty"
    subkey = basekeytest(subname).create()
    # Add some non-empty subkeys
    subkey("AAA").create()["LOL"] = 2
    subkey("BBBB").create()["value"] = "hello"
    # Add some values
    subkey["42"] = 43
    subkey["XXX"] = "42_42"
    assert subkey.values
    assert subkey.subkeys
    subkey.empty()
    # Check everythin disappeared
    assert not subkey.values
    assert not subkey.subkeys


def test_registry_unicode_value_name_enumerate():
    name1 = u"enum_" + UNICODE_PATH_NAME
    name2 = u"enum_" + UNICODE_RU_STRING
    basekeytest[name1] = 1
    basekeytest[name2] = 2
    values_names = [v.name for v in basekeytest.values]
    assert name1 in values_names
    assert name2 in values_names


class CustomCountForRegistryTest(object):
    TESTKEY = None

    def __init__(self):
        self.value = 0


    def __iter__(self):
        while True:
            print("NEXT")
            if self.value == 1:
                print("ADDING HARDCODE KEY !")
                self.TESTKEY[BIG_KEY_NAME] = BIG_KEY_VALUE
            yield self.value
            self.value += 1

BIG_KEY_NAME = "BIG" * 50
BIG_KEY_VALUE = "BIG" * 0x2000

def test_registry_unicode_value_name_enumerate_with_race_condition(monkeypatch):
    import itertools
    # With itertools.count() to add a big key in the middle of the enumeration
    # With a bigger name & data that the key currently existing

    # Create a new subkey so that the KeyInfos are "reset"
    subkeyname = str(datetime.datetime.now())
    assert not basekeytest(subkeyname).exists
    subkey = basekeytest(subkeyname).create()
    try:
        CustomCountForRegistryTest.TESTKEY = subkey
        monkeypatch.setattr(itertools, "count", CustomCountForRegistryTest)
        name1 = u"enum_" + UNICODE_PATH_NAME
        name2 = u"enum_" + UNICODE_RU_STRING
        subkey[name1] = 1
        subkey[name2] = 2
        values_names = [v.name for v in subkey.values]
        assert name1 in values_names
        assert name2 in values_names
        assert BIG_KEY_NAME in values_names
    finally:
        subkey.delete()

def test_registry_unicode_subkeys_create_delete():
    if pfw_windows.pycompat.is_py3:
        subname =  UNICODE_RU_STRING + str(datetime.datetime.now())
    else:
        subname =  UNICODE_RU_STRING + unicode(datetime.datetime.now())
    subkey = basekeytest(subname)
    assert not subkey.exists
    subkey.create()
    assert subkey.exists
    subkey.delete()
    assert not subkey.exists


def test_registry_unicode_subkeys_enumerate():
    name1 = u"subkey" + UNICODE_PATH_NAME
    name2 = u"subkey" + UNICODE_RU_STRING
    basekeytest(name1).create()
    basekeytest(name2).create()
    subkey_names = [sk.name for sk in basekeytest.subkeys]
    assert name1 in subkey_names
    assert name2 in subkey_names

original_RegEnumValueW = pfw_windows.winproxy.RegEnumValueW

def fake_RegEnumValueW_fill_but_raise(hKey, dwIndex, lpValueName, lpcchValueName, lpReserved, lpType, lpData, lpcbData):
    print("fake_RegEnumValueW")
    result = original_RegEnumValueW(hKey, dwIndex, lpValueName, lpcchValueName, lpReserved, lpType, lpData, lpcbData)
    raise pfw_windows.winproxy.WinproxyError("fake_RegEnumValueW", gdef.ERROR_MORE_DATA)
    return result

def test_registry_win_bug_RegEnumValueW_1(monkeypatch):
    # import pdb; pdb.set_trace()
    # Found a bug on some computers where RegEnumValueW would fill the data but also ERROR_MORE_DATA
    basekeytest["VALUE_1"] = "LOOOL"
    basekeytest["VALUE_2"] = 42
    basekeytest["XXX" * 0x100] = 42
    assert set(x.name for x in basekeytest.values) == {"VALUE_1", "VALUE_2", "XXX" * 0x100}
    monkeypatch.setattr(pfw_windows.winproxy, "RegEnumValueW", fake_RegEnumValueW_fill_but_raise)
    # Bug make it hang here..
    assert set(x.name for x in basekeytest.values) == {"VALUE_1", "VALUE_2", "XXX" * 0x100}
    print("LOL")

def fake_RegEnumValueW_always_raise(hKey, dwIndex, lpValueName, lpcchValueName, lpReserved, lpType, lpData, lpcbData):
    print("fake_RegEnumValueW_always_raise")
    raise pfw_windows.winproxy.WinproxyError("fake_RegEnumValueW", gdef.ERROR_MORE_DATA)

def test_registry_win_bug_RegEnumValueW_2(monkeypatch):
    # Found a bug on some computers where RegEnumValueW would fill the data but also ERROR_MORE_DATA
    # This case here should never happen, but better an exception that an infinite loop
    basekeytest["VALUE_1"] = "LOOOL"
    basekeytest["VALUE_2"] = 42
    basekeytest["XXX" * 0x100] = 42
    assert set(x.name for x in basekeytest.values) == {"VALUE_1", "VALUE_2", "XXX" * 0x100}
    monkeypatch.setattr(pfw_windows.winproxy, "RegEnumValueW", fake_RegEnumValueW_always_raise)
    # Bug make it hang here..
    with pytest.raises(ValueError):
        # A bug that do not allow is to extract the values will raises to be explicit..
        assert set(x.name for x in basekeytest.values) == {"VALUE_1", "VALUE_2", "XXX" * 0x100}

original_basekeytest_get_key_size = basekeytest.get_key_size_info

def bad_get_key_valuesize():
    namesize, valuesize = original_basekeytest_get_key_size()
    return namesize, valuesize - 3

def bad_get_key_namesize():
    namesize, valuesize = original_basekeytest_get_key_size()
    return namesize - 3, valuesize

def test_registry_win_bug_get_key_size_info_valuesize_too_small(monkeypatch):
    basekeytest["VALUE_1"] = "LOOOL"
    basekeytest["VALUE_2"] = 42
    basekeytest["XXX" * 0x100] = 42

    assert set(x.name for x in basekeytest.values) == {"VALUE_1", "VALUE_2", "XXX" * 0x100}
    monkeypatch.setattr(basekeytest, "get_key_size_info", bad_get_key_valuesize)
    assert set(x.name for x in basekeytest.values) == {"VALUE_1", "VALUE_2", "XXX" * 0x100}

def test_registry_win_bug_get_key_size_info_namesize_too_small(monkeypatch):
    basekeytest["VALUE_1"] = "LOOOL"
    basekeytest["VALUE_2"] = 42
    basekeytest["XXX" * 0x100] = 42

    assert set(x.name for x in basekeytest.values) == {"VALUE_1", "VALUE_2", "XXX" * 0x100}
    monkeypatch.setattr(basekeytest, "get_key_size_info", bad_get_key_namesize)
    assert set(x.name for x in basekeytest.values) == {"VALUE_1", "VALUE_2", "XXX" * 0x100}
