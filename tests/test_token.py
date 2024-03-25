import pytest
import os

import pfw_windows
import pfw_windows.security
import pfw_windows.generated_def as gdef

@pytest.fixture
def curtok():
    return pfw_windows.current_process.token

@pytest.fixture
def newtok():
    return pfw_windows.current_process.token.duplicate()


if pfw_windows.pycompat.is_py3:
    unicode_type = str
else:
    unicode_type = unicode

def test_token_info(curtok):
    assert isinstance(curtok.computername, unicode_type)
    assert isinstance(curtok.username, unicode_type)
    assert isinstance(curtok.integrity, pfw_windows.pycompat.int_types)
    assert isinstance(curtok.is_elevated, (bool))

def test_lower_integrity(newtok):
    assert newtok.integrity != 123
    # Change token integrity
    newtok.integrity = 123
    # newtok.integrity retrieve the integrity at each call so this in enough
    assert newtok.integrity == 123

def test_token_user(curtok):
    user_sid = curtok.user
    assert user_sid
    computername, username = pfw_windows.utils.lookup_sid(user_sid)
    assert computername == pfw_windows.system.computer_name
    assert username == os.environ["USERNAME"]

def test_token_id(curtok):
    ntok = curtok.duplicate()
    assert ntok.id != curtok.id
    mid = ntok.modified_id
    aid = ntok.authentication_id
    ntok.enable_privilege(b"SeShutDownPrivilege")
    mid2 = ntok.modified_id
    aid2 = ntok.authentication_id
    ntok.integrity -= 1
    assert ntok.modified_id != mid2 != mid
    assert ntok.authentication_id == aid2 == aid


def test_enable_privilege(newtok):
    PRIVILEGE_NAME = b"SeShutdownPrivilege"
    assert not newtok.privileges[PRIVILEGE_NAME] & gdef.SE_PRIVILEGE_ENABLED
    newtok.enable_privilege(PRIVILEGE_NAME)
    assert newtok.privileges[PRIVILEGE_NAME] & gdef.SE_PRIVILEGE_ENABLED


def test_adjust_privilege(newtok):
    PRIVILEGE_NAME = b"SeShutdownPrivilege"
    PRIVILEGE2_NAME = b"SeTimeZonePrivilege"
    tok_dup = newtok.duplicate()
    assert not tok_dup.privileges[PRIVILEGE_NAME] & gdef.SE_PRIVILEGE_ENABLED
    assert not tok_dup.privileges[PRIVILEGE2_NAME] & gdef.SE_PRIVILEGE_ENABLED
    # Enable privilege in another token.
    privs = newtok.privileges
    assert not privs[PRIVILEGE_NAME] & gdef.SE_PRIVILEGE_ENABLED
    assert not privs[PRIVILEGE2_NAME] & gdef.SE_PRIVILEGE_ENABLED

    privs[PRIVILEGE_NAME] = gdef.SE_PRIVILEGE_ENABLED
    privs[PRIVILEGE2_NAME] = gdef.SE_PRIVILEGE_ENABLED
    tok_dup.adjust_privileges(privs)

    assert tok_dup.privileges[PRIVILEGE_NAME] & gdef.SE_PRIVILEGE_ENABLED
    assert tok_dup.privileges[PRIVILEGE2_NAME] & gdef.SE_PRIVILEGE_ENABLED

    assert not newtok.privileges[PRIVILEGE_NAME] & gdef.SE_PRIVILEGE_ENABLED
    newtok.enable_privilege(PRIVILEGE_NAME)
    assert newtok.privileges[PRIVILEGE_NAME] & gdef.SE_PRIVILEGE_ENABLED


def test_token_privilege_dict(newtok):
    PRIVILEGE_NAME = b"SeShutdownPrivilege"
    privdict = newtok.privileges
    # These API use Token._lookup_name() that are not tested by other means
    assert privdict.keys()
    assert privdict.items()
    assert PRIVILEGE_NAME in privdict.keys() # Implement contains ?


def test_token_groups(curtok):
    groups = curtok.groups
    groups_size = groups.GroupCount
    assert groups_size > 0
    assert len(groups.sids) == groups_size
    assert len(groups.sids_and_attributes) == groups_size

def test_token_duplicate(newtok):
    x = newtok.duplicate()
    assert x.type == newtok.type

    primtok = newtok.duplicate(type=gdef.TokenPrimary)
    assert primtok.type == gdef.TokenPrimary
    with pytest.raises(WindowsError):
        assert x.impersonation_level

    with pytest.raises(ValueError):
        # duplicate TokenPrimary -> TokenImpersonation require explicit impersonation_level
        primtok.duplicate(type=gdef.TokenImpersonation)

    for i in range(gdef.SecurityAnonymous, gdef.SecurityDelegation + 1):
        x = newtok.duplicate(type=gdef.TokenImpersonation, impersonation_level=i)
        assert x.type == gdef.TokenImpersonation
        assert x.impersonation_level == i





# def test_token_groups
