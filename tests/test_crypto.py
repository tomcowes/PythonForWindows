import pytest

import pfw_windows.crypto
import pfw_windows.generated_def as gdef
import pfw_windows.crypto.generation

from .pfwtest import *

pytestmark = pytest.mark.usefixtures('check_for_gc_garbage')

TEST_CERT = b"""
MIIBwTCCASqgAwIBAgIQG46Uyws+67ZBOfPJCbFrRjANBgkqhkiG9w0BAQsFADAfMR0wGwYDVQQD
ExRQeXRob25Gb3JXaW5kb3dzVGVzdDAeFw0xNzA0MTIxNDM5MjNaFw0xODA0MTIyMDM5MjNaMB8x
HTAbBgNVBAMTFFB5dGhvbkZvcldpbmRvd3NUZXN0MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKB
gQCRHwC/sRfXh5pc4poc85aidrudbPdya+0OeonQlf1JQ1ekf7KSfADV5FLkSQu2BzgBK9DIWTGX
XknBJIzZF03UZsVg5D67V2mnSClXucc0cGFcK4pDDt0tHeabA2GPinVe7Z6qDT4ZxPR8lKaXDdV2
Pg2hTdcGSpqaltHxph7G/QIDAQABMA0GCSqGSIb3DQEBCwUAA4GBACcQFdOlVjYICOIyAXowQaEN
qcLpN1iWoL9UijNhTY37+U5+ycFT8QksT3Xmh9lEIqXMh121uViy2P/3p+Ek31AN9bB+BhWIM6PQ
gy+ApYDdSwTtWFARSrMqk7rRHUveYEfMw72yaOWDxCzcopEuADKrrYEute4CzZuXF9PbbgK6"""

## Cert info:
#  Name: PythonForWindowsTest
#  Serial: '1b 8e 94 cb 0b 3e eb b6 41 39 f3 c9 09 b1 6b 46'

TEST_PFX_PASSWORD = "TestPassword"

TEST_PFX = b"""
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
"""

@pytest.fixture()
def rawcert():
    return b64decode(TEST_CERT)


@pytest.fixture()
def rawpfx():
    return b64decode(TEST_PFX)

PFW_TEST_TMP_KEY_CONTAINER = "PythonForWindowsTMPContainerTest"
RANDOM_CERTIF_NAME = b"PythonForWindowsGeneratedRandomCertifTest"
RANDOM_PFX_PASSWORD = "PythonForWindowsGeneratedRandomPFXPassword"

@pytest.fixture()
def randomkeypair(keysize=1024):
    r"""Generate a cert / pfx. Based on samples\crypto\encryption_demo.py"""
    cert_store = pfw_windows.crypto.CertificateStore.new_in_memory()
    # Create a TMP context that will hold our newly generated key-pair
    with pfw_windows.crypto.CryptContext(PFW_TEST_TMP_KEY_CONTAINER, None, gdef.PROV_RSA_FULL, 0, retrycreate=True) as ctx:
        key = gdef.HCRYPTKEY()
        keysize_flags = keysize << 16
        # Generate a key-pair that is exportable
        pfw_windows.winproxy.CryptGenKey(ctx, gdef.AT_KEYEXCHANGE, gdef.CRYPT_EXPORTABLE | keysize_flags, key)
        # It does NOT destroy the key-pair from the container,
        # It only release the key handle
        # https://msdn.microsoft.com/en-us/library/windows/desktop/aa379918(v=vs.85).aspx
        pfw_windows.winproxy.CryptDestroyKey(key)

    # Descrption of the key-container that will be used to generate the certificate
    KeyProvInfo = gdef.CRYPT_KEY_PROV_INFO()
    KeyProvInfo.pwszContainerName = PFW_TEST_TMP_KEY_CONTAINER
    KeyProvInfo.pwszProvName = None
    KeyProvInfo.dwProvType = gdef.PROV_RSA_FULL
    KeyProvInfo.dwFlags = 0
    KeyProvInfo.cProvParam = 0
    KeyProvInfo.rgProvParam = None
    #KeyProvInfo.dwKeySpec = AT_SIGNATURE
    KeyProvInfo.dwKeySpec = gdef.AT_KEYEXCHANGE

    crypt_algo = gdef.CRYPT_ALGORITHM_IDENTIFIER()
    crypt_algo.pszObjId = gdef.szOID_RSA_SHA256RSA.encode("ascii") # do something else (bytes in generated ctypes ?)

    # This is fucking dumb, there is no .format on bytes object...
    certif_name = b"".join((b"CN=", RANDOM_CERTIF_NAME))
    # Generate a self-signed certificate based on the given key-container and signature algorithme
    certif = pfw_windows.crypto.generation.generate_selfsigned_certificate(certif_name, key_info=KeyProvInfo, signature_algo=crypt_algo)
    # Add the newly created certificate to our TMP cert-store
    cert_store.add_certificate(certif)
    # Generate a pfx from the TMP cert-store
    pfx = pfw_windows.crypto.generation.generate_pfx(cert_store, RANDOM_PFX_PASSWORD)
    yield certif, pfx
    # Destroy the TMP key container
    prov = gdef.HCRYPTPROV()
    pfw_windows.winproxy.CryptAcquireContextW(prov, PFW_TEST_TMP_KEY_CONTAINER, None, gdef.PROV_RSA_FULL, gdef.CRYPT_DELETEKEYSET)



def test_certificate(rawcert):
    cert = pfw_windows.crypto.Certificate.from_buffer(rawcert)
    assert cert.serial == '1b 8e 94 cb 0b 3e eb b6 41 39 f3 c9 09 b1 6b 46'
    assert cert.name == b'PythonForWindowsTest'
    assert cert.issuer == b'PythonForWindowsTest'
    assert cert.thumbprint == 'EF 0C A8 C9 F9 E0 96 AF 74 18 56 8B C1 C9 57 27 A0 89 29 6A'
    assert cert.encoded == rawcert
    assert cert.version == 2
    assert cert == cert
    assert cert is cert.duplicate()
    cert.chains # TODO: craft a certificate with a chain for test purpose
    cert.store.certs
    cert.properties


def test_pfx(rawcert, rawpfx):
    pfx = pfw_windows.crypto.import_pfx(rawpfx, TEST_PFX_PASSWORD)
    orig_cert = pfw_windows.crypto.Certificate.from_buffer(rawcert)
    certs = pfx.certs
    assert len(certs) == 1
    # Test cert comparaison
    assert certs[0] == orig_cert


def test_open_pfx_bad_password(rawpfx):
    with pytest.raises(WindowsError) as ar:
        pfx = pfw_windows.crypto.import_pfx(rawpfx, "BadPassword")


def test_encrypt_decrypt(rawcert, rawpfx):
    message_to_encrypt = b"Testing message \xff\x01"
    cert = pfw_windows.crypto.Certificate.from_buffer(rawcert)
    # encrypt should accept a cert or iterable of cert
    res = pfw_windows.crypto.encrypt(cert, message_to_encrypt)
    res2 = pfw_windows.crypto.encrypt([cert, cert], message_to_encrypt)
    del cert
    assert message_to_encrypt not in res

    # Open pfx and decrypt
    pfx = pfw_windows.crypto.import_pfx(rawpfx, TEST_PFX_PASSWORD)
    decrypt = pfw_windows.crypto.decrypt(pfx, res)
    decrypt2 = pfw_windows.crypto.decrypt(pfx, res2)

    assert message_to_encrypt == decrypt
    assert decrypt == decrypt2



def test_randomkeypair(randomkeypair):
    randcert, randrawpfx = randomkeypair
    assert randcert.name == RANDOM_CERTIF_NAME
    randpfx = pfw_windows.crypto.import_pfx(randrawpfx, RANDOM_PFX_PASSWORD) # Check password is good too


def test_encrypt_decrypt_multiple_receivers(rawcert, rawpfx, randomkeypair):
    message_to_encrypt = b"\xff\x00 Testing message \xff\x01"
    # Receiver 1: random key pair
    randcert, randrawpfx = randomkeypair
    randpfx = pfw_windows.crypto.import_pfx(randrawpfx, RANDOM_PFX_PASSWORD)
    # Receiver 1: PFW-test-keypair
    pfx = pfw_windows.crypto.import_pfx(rawpfx, TEST_PFX_PASSWORD)
    cert = pfw_windows.crypto.Certificate.from_buffer(rawcert)
    assert cert.name != randcert.name
    assert cert.encoded != randcert.encoded
    # Encrypt the message with 2 differents certificates
    encrypted = pfw_windows.crypto.encrypt([cert, randcert], message_to_encrypt)
    # Decrypt with each PFX and check the result is valid/the same
    decrypted = pfw_windows.crypto.decrypt(pfx, encrypted)
    decrypted2 = pfw_windows.crypto.decrypt(randpfx, encrypted)
    assert decrypted == decrypted2 == message_to_encrypt



def test_crypt_obj():
    path = r"C:\windows\system32\kernel32.dll"
    x = pfw_windows.crypto.CryptObject(path)
    x.crypt_msg.certs
    x.crypt_msg.signers
    x.signers_and_certs
    # TODO: Need some better ideas

def test_certificate_from_store():
    return pfw_windows.crypto.CertificateStore.from_system_store("Root")


def test_sign_verify(rawcert, rawpfx):
    message_to_sign = b"Testing message \xff\x01"
    # Load PFX (priv+pub key) & certif (pubkey only)
    pfx = pfw_windows.crypto.import_pfx(rawpfx, TEST_PFX_PASSWORD)
    cert = pfw_windows.crypto.Certificate.from_buffer(rawcert)
    signed_blob = pfw_windows.crypto.sign(pfx.certs[0], message_to_sign)
    assert message_to_sign in signed_blob
    decoded_blob = pfw_windows.crypto.verify_signature(cert, signed_blob)
    assert decoded_blob == message_to_sign


def test_sign_verify_fail(rawcert, rawpfx):
    message_to_sign = b"Testing message \xff\x01"
    # Load PFX (priv+pub key) & certif (pubkey only)
    pfx = pfw_windows.crypto.import_pfx(rawpfx, TEST_PFX_PASSWORD)
    cert = pfw_windows.crypto.Certificate.from_buffer(rawcert)
    signed_blob = pfw_windows.crypto.sign(pfx.certs[0], message_to_sign)
    assert message_to_sign in signed_blob
    # Tamper the signed mesasge content
    signed_blob = signed_blob.replace(b"message", b"massage")
    with pytest.raises(pfw_windows.winproxy.WinproxyError) as excinfo:
        decoded_blob = pfw_windows.crypto.verify_signature(cert, signed_blob)
    assert excinfo.value.winerror == gdef.STATUS_INVALID_SIGNATURE


# str(pfw_windows.crypto.encrypt(TEST_CERT, "Hello crypto")).encode("base64")
# Target serial == TEST_CERT.Serial == 1b 8e 94 cb 0b 3e eb b6 41 39 f3 c9 09 b1 6b 46
TEST_CRYPTMSG = b"""MIIBJAYJKoZIhvcNAQcDoIIBFTCCARECAQAxgc0wgcoCAQAwMzAfMR0wGwYDVQQDExRQeXRob25G
b3JXaW5kb3dzVGVzdAIQG46Uyws+67ZBOfPJCbFrRjANBgkqhkiG9w0BAQcwAASBgA1fwFY8w4Bb
fOMer94JhazbJxaUnV305QzF27w4GwNQ2UIpl9KWJoJJaF7azU3nVhP33agAxlxmr9fP48B6DeE1
pbu1jX9tEWlTJC6O0TmKcRPjblEaU6VJXXlpKlKZCmwCUuHR9VtcXGnxEU1Hy7FmHM96lvDRmYQT
Y0MnRJLyMDwGCSqGSIb3DQEHATAdBglghkgBZQMEASoEEEdEGEzKBrDO/zC8z6q6HLaAEGbjGCay
s6u32YhUxQ4/QhI="""

def test_cryptmsg_from_data():
    rawdata = b64decode(TEST_CRYPTMSG)
    cryptmsg = pfw_windows.crypto.CryptMessage.from_buffer(rawdata)
    rawtarget = b"\x1b\x8e\x94\xcb\x0b>\xeb\xb6A9\xf3\xc9\t\xb1kF"
    assert cryptmsg.get_recipient_data(0).SerialNumber.data[::-1] == rawtarget


# Dpapi

def test_dpapi_protect_unprotect():
    message_to_protect = b"Testing DPAPI message \xff\x01 but also \x02\xfe\xee"
    protected = pfw_windows.crypto.protect(message_to_protect)
    assert message_to_protect not in protected
    assert pfw_windows.crypto.unprotect(protected) == message_to_protect

def test_dpapi_protect_unprotect_with_entropy():
    message_to_protect = b"Testing DPAPI message \xff\x01 but also \x02\xfe\xee with entropy <3"
    protect_entropy = b"This is a password ? \x01\xff\x99"
    protected = pfw_windows.crypto.protect(message_to_protect, entropy=protect_entropy)
    assert message_to_protect not in protected
    with pytest.raises(WindowsError) as ar:
        pfw_windows.crypto.unprotect(protected)
    with pytest.raises(WindowsError) as ar:
        pfw_windows.crypto.unprotect(protected, entropy=b"Not the good password")
    assert pfw_windows.crypto.unprotect(protected, entropy=protect_entropy) == message_to_protect
