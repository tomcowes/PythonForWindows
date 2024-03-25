import sys
import pytest

import pfw_windows
import pfw_windows.generated_def as gdef

from .pfwtest import *
from pfw_windows.pycompat import is_py3

pytestmark = pytest.mark.usefixtures('check_for_gc_garbage')

def test_script_file_not_signed():
    assert not pfw_windows.wintrust.is_signed(__file__)
    assert pfw_windows.wintrust.check_signature(__file__) == gdef.TRUST_E_SUBJECT_FORM_UNKNOWN

if is_py3:
    # Py3 binaries are signed
    def test_python_signature():
        python_path = sys.executable
        assert pfw_windows.wintrust.is_signed(python_path)
        assert pfw_windows.wintrust.check_signature(python_path) == 0
else:
    # Py2 binaries are NOT signed
    def test_python_signature():
        python_path = sys.executable
        assert not pfw_windows.wintrust.is_signed(python_path)
        assert pfw_windows.wintrust.check_signature(python_path) == gdef.TRUST_E_NOSIGNATURE

def test_kernel32_signed():
    k32_path = r"C:\windows\system32\kernel32.dll"
    assert pfw_windows.wintrust.is_signed(k32_path)
    assert pfw_windows.wintrust.check_signature(k32_path) == 0