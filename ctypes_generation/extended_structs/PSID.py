_INITIAL_PSID = PSID
class PSID(_INITIAL_PSID): # _INITIAL_PSID -> PVOID

    def __eq__(self, other):
        return bool(pfw_windows.winproxy.EqualSid(self, other))

    def __ne__(self, other):
        return not pfw_windows.winproxy.EqualSid(self, other)

    @property
    def size(self):
        return pfw_windows.winproxy.GetLengthSid(self)

    def duplicate(self):
        size = self.size
        buffer = ctypes.c_buffer(size)
        pfw_windows.winproxy.CopySid(size, buffer, self)
        return ctypes.cast(buffer, type(self))

    @classmethod
    def from_string(cls, strsid):
        self = cls()
        if not isinstance(strsid, bytes):
            strsid = strsid.encode("ascii")
        # Pass to ConvertStringSidToSidW ?
        pfw_windows.winproxy.ConvertStringSidToSidA(strsid, self)
        return self

    def to_string(self):
       sid_str  = LPCSTR()
       pfw_windows.winproxy.ConvertSidToStringSidA(self, sid_str)
       result = sid_str.value.decode("ascii") # ConvertSidToStringSidW ?
       pfw_windows.winproxy.LocalFree(sid_str)
       return result

    __str__ = to_string

    def __repr__(self):
        try:
            return """<{0} "{1}">""".format(type(self).__name__, self.to_string())
        except WindowsError: # Case of PSID is not valide
            if not self:
                return """<{0} (NULL) at {1:#x}>""".format(type(self).__name__, id(self))
            return """<{0} "<conversion-failed>" at {1:#x}>""".format(type(self).__name__, id(self))

    __sprint__ = __repr__
