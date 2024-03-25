import sys
import os
import os.path
import re
import glob
import textwrap

import dummy_wintypes
import struct_parser
import func_parser
import def_parser
import com_parser

pjoin = os.path.join
pexists = os.path.exists
dedent = textwrap.dedent


TYPE_EQUIVALENCE = [
    # BYTE is defined in ctypes.wintypes as c_byte but who wants
    # BYTE to be signed ? (from MSDN: <typedef unsigned char BYTE;>)
    ('BYTE', 'c_ubyte'),
    ('PWSTR', 'LPWSTR'),
    ('PCWSTR', 'LPWSTR'),
    ('SIZE_T', 'c_size_t'),
    ('PSIZE_T', 'POINTER(SIZE_T)'),
    ('PVOID', 'c_void_p'),
    ('PPS_POST_PROCESS_INIT_ROUTINE', 'PVOID'),
    ('NTSTATUS', 'DWORD'),
    ('SECURITY_INFORMATION', 'DWORD'),
    ('PSECURITY_INFORMATION', 'POINTER(SECURITY_INFORMATION)'),
    ('PULONG', 'POINTER(ULONG)'),
    ('PDWORD', 'POINTER(DWORD)'),
    ('LPDWORD', 'POINTER(DWORD)'),
    ('LPTHREAD_START_ROUTINE', 'PVOID'),
    ('WNDENUMPROC', 'PVOID'),
    ('PHANDLER_ROUTINE', 'PVOID'),
    ('LPBYTE', 'POINTER(BYTE)'),
    ('ULONG_PTR','PVOID'),
    ('DWORD_PTR','ULONG_PTR'),
    ('KAFFINITY','ULONG_PTR'),
    ('KPRIORITY','LONG'),
    ('CHAR', 'c_char'),
    ('INT', 'c_int'),
    ('UCHAR', 'c_char'),
    ('CSHORT', 'c_short'),
    ('VARTYPE', 'c_ushort'),
    ('PBOOL', 'POINTER(BOOL)'),
    ('PSTR', 'LPSTR'),
    ('PCSTR', 'LPSTR'),
    ('va_list', 'c_char_p'),
    ('BSTR', 'c_wchar_p'),
    ('OLECHAR', 'c_wchar'),
    ('POLECHAR', 'c_wchar_p'),
    ('PUCHAR', 'POINTER(UCHAR)'),
    ('double', 'c_double'),
    ('FARPROC', 'PVOID'),
    ('HGLOBAL', 'PVOID'),
    ('PSID', 'PVOID'),
    ('PVECTORED_EXCEPTION_HANDLER', 'PVOID'),
    #('HRESULT', 'c_long'), # VERY BAD : real HRESULT raise by itself -> way better
    ('ULONGLONG', 'c_ulonglong'),
    ('LONGLONG', 'c_longlong'),
    ('ULONG64', 'c_ulonglong'),
    ('UINT64', 'ULONG64'),
    ('LONG64', 'c_longlong'),
    ('LARGE_INTEGER', 'LONGLONG'),
    ('PLARGE_INTEGER', 'POINTER(LARGE_INTEGER)'),
    ('DWORD64', 'ULONG64'),
    ('SCODE', 'LONG'),
    ('CIMTYPE', 'LONG'),
    ('NET_IFINDEX', 'ULONG'),
    ('IF_INDEX', 'NET_IFINDEX'),
    ('IFTYPE', 'ULONG'),
    ('PULONG64', 'POINTER(ULONG64)'),
    ('LPFILETIME', 'POINTER(FILETIME)'),
    ('LPPOINT', 'POINTER(POINT)'),
    ('LPRECT', 'POINTER(RECT)'),
    ('PBYTE', 'POINTER(BYTE)'),
    ('PUINT', 'POINTER(UINT)'),
    ('PHANDLE', 'POINTER(HANDLE)'),
    ('HKEY', 'HANDLE'),
    ('HCATADMIN', 'HANDLE'),
    ('HCATINFO', 'HANDLE'),
    ('HDC', 'HANDLE'),
    ('HBITMAP', 'HANDLE'),
    ('SC_HANDLE', 'HANDLE'),
    ('HCERTCHAINENGINE', 'HANDLE'),
    ('LPHANDLE', 'POINTER(HANDLE)'),
    ('ALPC_HANDLE', 'HANDLE'),
    ('PALPC_HANDLE', 'POINTER(ALPC_HANDLE)'),
    ('PHKEY', 'POINTER(HKEY)'),
    ('ACCESS_MASK', 'DWORD'),
    ('REGSAM', 'ACCESS_MASK'),
    ('PBOOLEAN', 'POINTER(BOOLEAN)'),
    ('SECURITY_CONTEXT_TRACKING_MODE', 'BOOLEAN'),
    ('HCRYPTPROV_OR_NCRYPT_KEY_HANDLE', 'PULONG'),
    ('HCRYPTPROV_LEGACY', 'PULONG'),
    ('HCRYPTKEY', 'PULONG'),
    ('HCRYPTPROV', 'PULONG'),
    ('HCRYPTHASH', 'PULONG'),
    ('ALG_ID', 'UINT'),
    ("DISPID", "LONG"),
    ("MEMBERID", "DISPID"),
    ('PSECURITY_DESCRIPTOR', 'PVOID'),
    ('LPPROC_THREAD_ATTRIBUTE_LIST', 'PVOID'),
    ('LPUNKNOWN', 'POINTER(PVOID)'),
    ('SPC_UUID', 'BYTE * 16'),
    ('PIO_APC_ROUTINE', 'PVOID'),
    ('DEVICE_TYPE', 'DWORD'),
    #STUFF FOR COM (will be replace at runtime
    # real def in com_interface_header
    # ('GUID', 'PVOID'),
    #('REFGUID', 'PVOID'),
    #('LPGUID', 'PVOID'),
    # STUFF FOR DBGENGINE
    ('PWINDBG_EXTENSION_APIS32', 'PVOID'),
    ('PWINDBG_EXTENSION_APIS64', 'PVOID'),
    #('PDEBUG_SYMBOL_PARAMETERS', 'PVOID'),
    # Will be changed at import time
    ('LPCONTEXT', 'PVOID'),
    ('HCERTSTORE', 'PVOID'),
    ('HCRYPTMSG', 'PVOID'),
    ('PALPC_PORT_ATTRIBUTES', 'PVOID'),
    ]

TYPE_EQUIVALENCE.append(('VOID', 'DWORD'))
# TRICHE
BASIC_TYPE = dummy_wintypes.names + list([x[0] for x in TYPE_EQUIVALENCE])

class CtypesGenerator(object):
    common_header = "#Generated file\n"

    PARSER = None
    IMPORT_HEADER = "{deps}"

    def __init__(self, indirname, outfilename, dependances=()):
        self.indirname = indirname
        self.outfilename = outfilename
        # self.infile = open(self.infilename)
        self.data = None
        self.dependances = dependances

        self.exports = set([])
        self.imports = set([])

        self.parse()
        self.analyse(self.data)
        self.check_dependances()

    # def parse(self):
        # if self.data is None:
            # print("Parsing <{0}>".format(self.infilename))
            # self.data = self.PARSER(self.infile.read()).parse()
        # return self.data

    def parse(self):
        if self.data is not None:
            return self.data
        data = []
        for filename in glob.glob(self.indirname):
            print("Parsing <{0}>".format(filename))
            # data.append(self.PARSER(open(filename).read()).parse())
            data += self.PARSER(open(filename).read()).parse()
        self.data = data
        return data

    def analyse(self, data):
        raise NotImplementedError("<{0}> doest not implement <analyse>".format(type(self).__name__))

    def check_dependances(self):
        missing = self.imports
        for dep in self.dependances:
            missing -= dep.exports
        if missing:
            # raise ValueError("Missing dependance <{0}> in <{1}>".format(missing, self.infilename))
            print ValueError("Missing dependance <{0}>".format(missing))

    def generate_import(self):
        deps = "\n".join(["from {0} import *".format(os.path.basename(dep.outfilename).rsplit(".")[0]) for dep in self.dependances])
        return self.IMPORT_HEADER.format(deps = deps)

    def add_imports(self, *names):
        self.imports.update(names)

    def add_exports(self, *names):
        self.exports.update(names)

    def generate(self):
        raise NotImplementedError("<{0}> doest not implement <generate>".format(type(self).__name__))

    def append_input_file(self, filename):
        print("Adding file <{0}>".format(filename))
        self.parse()
        self.data +=  self.PARSER(open(filename).read()).parse()
        self.analyse(self.data)
        self.check_dependances()

class InitialDefGenerator(CtypesGenerator):
    PARSER = def_parser.WinDefParser
    HEADER = dedent("""
        import sys
        import platform
        if sys.version_info.major == 3:
            long = int

        bits = platform.architecture()[0]
        bitness =  int(bits[:2])

        NATIVE_WORD_MAX_VALUE = 0xffffffff if bitness == 32 else 0xffffffffffffffff

        class Flag(long):
            def __new__(cls, name, value):
                return super(Flag, cls).__new__(cls, value)

            def __init__(self, name, value):
                self.name = name

            def __repr__(self):
                return "{0}({1})".format(self.name, hex(self))

            __str__ = __repr__

           # Fix pickling with protocol 2
            def __getnewargs__(self, *args):
                return self.name, long(self)

        class StrFlag(str):
            def __new__(cls, name, value):
                if isinstance(value, cls):
                    return value
                return super(StrFlag, cls).__new__(cls, value)

            def __init__(self, name, value):
                self.name = name

            def __repr__(self):
                return "{0}({1})".format(self.name, str.__repr__(self))

            # __str__ = __repr__

            # Fix pickling with protocol 2
            def __getnewargs__(self, *args):
                return self.name, str.__str__(self)

        def make_flag(name, value):
            if isinstance(value, (int, long)):
                return Flag(name, value)
            return StrFlag(name, value)

        class FlagMapper(dict):
            def __init__(self, *values):
                self.update({x:x for x in values})

            def __missing__(self, key):
                return key
        """)

    IMPORT_HEADER = "{deps}"

    def analyse(self, data):
        self.add_exports("Flag")
        self.add_exports("NATIVE_WORD_MAX_VALUE")
        for defin in data:
            self.add_exports(defin.name)

    def generate(self):
        ctypes_lines = [self.common_header, self.HEADER]
        #deps = "\n".join(["from {0} import *".format(os.path.basename(dep.outfilename).rsplit(".")[0]) for dep in self.dependances])
        ctypes_lines += [self.generate_import()]
        ctypes_lines += [d.generate_ctypes() for d in self.parse()]
        ctypes_code = "\n".join(ctypes_lines)
        with open(self.outfilename, "w") as f:
            f.write(ctypes_code)
        print("<{0}> generated".format(self.outfilename))
        return ctypes_code

    def generate_doc(self, target_file):
        all_lines = [".. currentmodule:: pfw_windows.generated_def\n\n"
                     "Windef\n"
                     "------\n"]
        all_lines += [".. autodata:: {windef.name}\n".format(windef=windef) for windef in self.parse()]
        with open(target_file, "w") as f:
            f.writelines(all_lines)

class StructGenerator(CtypesGenerator):
    PARSER = struct_parser.WinStructParser
    IMPORT_HEADER = dedent ("""
        from ctypes import *
        from ctypes.wintypes import *
        {deps}
    """)
    TYPES_HEADER = dedent("""
        class EnumValue(Flag):
            def __new__(cls, enum_name, name, value):
                return super(EnumValue, cls).__new__(cls, name, value)

            def __init__(self, enum_name, name, value):
                self.enum_name = enum_name
                self.name = name

            def __repr__(self):
                return "{0}.{1}({2})".format(self.enum_name, self.name, hex(self))

            # Fix pickling with protocol 2
            def __getnewargs__(self, *args):
                return self.enum_name, self.name, int(self)


        class EnumType(DWORD):
            values = ()
            mapper = {}

            @property
            def value(self):
                raw_value = super(EnumType, self).value
                return self.mapper.get(raw_value, raw_value)

            def __repr__(self):
                raw_value = super(EnumType, self).value
                if raw_value in self.values:
                    value = self.value
                    return "<{0} {1}({2})>".format(type(self).__name__, value.name, hex(raw_value))
                return "<{0}({1})>".format(type(self).__name__, hex(self.value))

        """)

    def __init__(self, *args, **kwargs):
        self.export_enums = set([])
        self.export_structs = set([])
        super(StructGenerator, self).__init__(*args, **kwargs)


    def analyse(self, data):
        structs, enums = data
        for btype in BASIC_TYPE:
            self.add_exports(btype)
        for enum in enums:
            self.add_exports(enum.name)
            self.add_exports(*enum.typedef)
            self.export_enums.update([enum.name] + enum.typedef.keys())
        for struct in structs:
            self.add_exports(struct.name)
            self.add_exports(*struct.typedef)
            self.export_structs.update([struct.name] + struct.typedef.keys())
            for field_type, field_name, nb_rep in struct.fields:
                if field_type.name not in self.exports:
                    self.add_imports(field_type.name)
                try:
                    int(nb_rep)
                except:
                    self.add_imports(nb_rep)

        # We have PPORT_MESSAGE32 and PPORT_MESSAGE64 and PPORT_MESSAGE is choosed at runtime
        self.add_exports("PPORT_MESSAGE")


    def generate(self):
        type_equivalences = "\n".join(["{0} = {1}".format(*x) for x in TYPE_EQUIVALENCE])
        HEADER = self.generate_import()
        HEADER += type_equivalences
        HEADER += self.TYPES_HEADER

        structs, enums = self.data
        ctypes_lines = [self.common_header, HEADER]
        for definition in [d for l in (enums, structs) for d in l]:
            ctypes_lines.append(definition.generate_ctypes())
            if definition.name in EXTENDED_STRUCT:
                print("Including extended definition for <{0}>".format(definition.name))
                extended_struct_filename = from_here(os.path.join("extended_structs", "{0}.py".format(definition.name)))
                with open(extended_struct_filename) as f:
                    ctypes_lines.append(f.read())
                    # import pdb;pdb.set_trace()
                    ctypes_lines.append(definition.generate_typedef_ctypes() + "\n")

        ctypes_code = "\n".join(ctypes_lines)
        with open(self.outfilename, "w") as f:
            f.write(ctypes_code)
        print("<{0}> generated".format(self.outfilename))
        return ctypes_code

    def parse(self):
        if self.data is not None:
            return self.data
        data = [[], []]
        for filename in glob.glob(self.indirname):
            print("Parsing <{0}>".format(filename))
            # data.append(self.PARSER(open(filename).read()).parse())
            new_data = self.PARSER(open(filename).read()).parse()
            data[0].extend(new_data[0])
            data[1].extend(new_data[1])
        self.data = data
        return data

    def append_input_file(self, filename):
        print("Adding file <{0}>".format(filename))
        self.parse()
        new_data = self.PARSER(open(filename).read()).parse()
        self.data[0].extend(new_data[0])
        self.data[1].extend(new_data[1])
        self.analyse(self.data)
        self.check_dependances()

    def generate_doc(self, target_file):
        all_lines = [".. currentmodule:: pfw_windows.generated_def\n\n"
                     "Winstructs\n"
                     "----------\n"]
        struct_separator = "'"
        structs, enums = self.parse()
        for struct in structs:
            all_lines.append("{0}\n{1}\n".format(struct.name, struct_separator * len(struct.name)))
            for name, type in  struct.typedef.items():
                all_lines.append(".. class:: {0}\n\n".format(name))
                if hasattr(type, "type"):
                    all_lines.append("    Pointer to :class:`{0}`\n\n".format(type.type.name))
                else:
                    all_lines.append("    Alias for :class:`{0}`\n\n".format(type.name))

            all_lines.append(".. class:: {0}\n".format(struct.name))
            for ftype, fname, nb in struct.fields:
                array_str = " ``[{nb}]``".format(nb=nb) if nb > 1 else ""
                all_lines.append("\n    .. attribute:: {0}\n\n        :class:`{1}`{2}\n\n".format(fname, ftype.name, array_str))

        all_lines += ["WinEnums\n--------\n"]
        for enum in enums:
            all_lines.append("{0}\n{1}\n".format(enum.name, struct_separator * len(enum.name)))
            for name, type in  enum.typedef.items():
                all_lines.append(".. class:: {0}\n\n".format(name))
                if hasattr(type, "type"):
                    all_lines.append("    Pointer to :class:`{0}`\n\n".format(type.type.name))
                else:
                    all_lines.append("    Alias for :class:`{0}`\n\n".format(type.name))
            all_lines.append(".. class:: {0}\n\n".format(enum.name))
            for enum_value, enum_name in enum.fields:
                all_lines.append("\n    .. attribute:: {0}({1})\n\n".format(enum_name, enum_value))

        with open(target_file, "w") as f:
            f.writelines(all_lines)


class FuncGenerator(CtypesGenerator):
    PARSER = func_parser.WinFuncParser
    IMPORT_HEADER = dedent ("""
        from ctypes import *
        from ctypes.wintypes import *
        {deps}

        """)

    def analyse(self, data):
        for func in data:
            if isinstance(func.return_type, tuple) and func.return_type[0] == "PTR":
                self.add_imports(func.return_type[1])
            else:
                self.add_imports(func.return_type)
            for param_type, _ in func.params:
                if param_type.startswith("POINTER(") and param_type.endswith(")"):
                    param_type = param_type[len("POINTER("): -1]
                self.add_imports(param_type)
            self.add_exports(func.name)


    def generate(self):
        deps = "\n".join(["from {0} import *".format(os.path.basename(dep.outfilename).rsplit(".")[0]) for dep in self.dependances])
        HEADER = self.generate_import()

        func_list = "functions = {0}\n\n".format(str([f.name for f in self.data]))

        ctypes_lines = [self.common_header, HEADER, func_list] + [d.generate_ctypes() for d in self.parse()]
        ctypes_code = "\n".join(ctypes_lines)
        with open(self.outfilename, "w") as f:
            f.write(ctypes_code)
        print("<{0}> generated".format(self.outfilename))
        return ctypes_code

class NtStatusGenerator(CtypesGenerator):
    IMPORT_HEADER = dedent("""
    import ctypes
    {deps}
    """)
    HEADER = dedent("""
    class NtStatusException(WindowsError):
        ALL_STATUS = {}
        def __init__(self , code):
            try:
                x = self.ALL_STATUS[code]
            except KeyError:
                x = (code, 'UNKNOW_ERROR', 'Error non documented in ntstatus.py')
            self.code = x[0]
            self.name = x[1]
            self.descr = x[2]
            x =  ctypes.c_long(x[0]).value, x[1], x[2]
            return super(NtStatusException, self).__init__(*x)

        def __str__(self):
            return "{e.name}(0x{e.code:x}): {e.descr}".format(e=self)

        def __repr__(self):
            return "{0}(0x{1:08x}, {2})".format(type(self).__name__, self.code, self.name)

        @classmethod
        def register_ntstatus(cls, code, name, descr):
            if code in cls.ALL_STATUS:
                return # Use the first def
            cls.ALL_STATUS[code] = (code, name, descr)
            return Flag(name, code)
    """)

    def __init__(self, infilename, outfilename, dependances=()):
        self.infilename = infilename
        self.outfilename = outfilename
        self.infile = open(self.infilename)
        self.data = None
        self.dependances = dependances

        self.exports = set([])
        self.imports = set([])

        self.parse()
        self.analyse(self.data)
        self.check_dependances()

    def parse_ntstatus(self, content):
        nt_status_defs = []
        for line in content.split("\n"):
            if not line:
                continue
            code, name, descr = line.split("|", 2)
            code = int(code, 0)
            descr = re.sub(" +", " ", descr[:-1]) # remove \n
            descr = descr.replace('"', "'")
            nt_status_defs.append((code, name, descr))
        self.data = nt_status_defs
        return self

    # Hack for PARSER
    def parse(self):
        if self.data is None:
            print("Parsing <{0}>".format(self.infilename))
            self.parse_ntstatus(self.infile.read())
        return self.data


    def analyse(self, data):
        self.add_imports("Flag")

    def generate(self):
        #deps = "\n".join(["from {0} import *".format(os.path.basename(dep.outfilename).rsplit(".")[0]) for dep in self.dependances])
        HEADER = self.generate_import() + self.HEADER
        ctypes_lines = [HEADER]
        for code, name, descr in self.parse():
            ctypes_lines.append('{1} = NtStatusException.register_ntstatus({0}, "{1}", "{2}")'.format(hex(code).strip("L"), name, descr))
        ctypes_code = "\n".join(ctypes_lines)
        with open(self.outfilename, "w") as f:
            f.write(ctypes_code)
        print("<{0}> generated".format(self.outfilename))
        return ctypes_code

    def generate_doc(self, target_file):
        all_lines = [".. currentmodule:: pfw_windows.generated_def\n\n"
                     "Ntstatus\n"
                     "--------\n"]
        all_lines += [".. autodata:: {nstatus_name}\n".format(nstatus_name=nstatus[1]) for nstatus in self.parse()]
        with open(target_file, "w") as f:
            f.writelines(all_lines)


class InitialCOMGenerator(CtypesGenerator):
    PARSER = com_parser.WinComParser
    IGNORE_INTERFACE = ["ITypeInfo"]
    IMPORT_HEADER = dedent("""
    import functools
    import ctypes


    {deps}

    """)
    HEADER = dedent("""
    generate_IID = IID.from_raw

    class COMInterface(ctypes.c_void_p):
        _functions_ = {
        }

        def __getattr__(self, name):
            if name in self._functions_:
                return functools.partial(self._functions_[name], self)
            return super(COMInterface, self).__getattribute__(name)

    class COMImplementation(object):
        IMPLEMENT = None

        def get_index_of_method(self, method):
            # This code is horrible but not totally my fault
            # the PyCFuncPtrObject->index is not exposed to Python..
            # repr is: '<COM method offset 2: WinFunctionType at 0x035DDBE8>'
            rpr = repr(method)
            if not rpr.startswith("<COM method offset ") or ":" not in rpr:
                raise ValueError("Could not extract offset of {0}".format(rpr))
            return int(rpr[len("<COM method offset "): rpr.index(":")])

        def extract_methods_order(self, interface):
            index_and_method = sorted((self.get_index_of_method(m),name, m) for name, m in interface._functions_.items())
            return index_and_method

        def verify_implem(self, interface):
            for func_name in interface._functions_:
                implem = getattr(self, func_name, None)
                if implem is None:
                    raise ValueError("<{0}> implementing <{1}> has no method <{2}>".format(type(self).__name__, self.IMPLEMENT.__name__, func_name))
                if not callable(implem):
                    raise ValueError("{0} implementing <{1}>: <{2}> is not callable".format(type(self).__name__, self.IMPLEMENT.__name__, func_name))
            return True

        def _create_vtable(self, interface):
            implems = []
            names = []
            for index, name, method in self.extract_methods_order(interface):
                func_implem = getattr(self, name)
                #PVOID is 'this'
                types = [method.restype, PVOID] + list(method.argtypes)
                implems.append(ctypes.WINFUNCTYPE(*types)(func_implem))
                names.append(name)
            class Vtable(ctypes.Structure):
                _fields_ = [(name, ctypes.c_void_p) for name in names]
            return Vtable(*[ctypes.cast(x, ctypes.c_void_p) for x in implems]), implems

        def __init__(self):
            self.verify_implem(self.IMPLEMENT)
            vtable, implems = self._create_vtable(self.IMPLEMENT)
            self.vtable = vtable
            self.implems = implems
            self.vtable_pointer = ctypes.pointer(self.vtable)
            self._as_parameter_ = ctypes.addressof(self.vtable_pointer)

        def QueryInterface(self, this, piid, result):
            if piid[0] in (IUnknown.IID, self.IMPLEMENT.IID):
                result[0] = this
                return 1
            return E_NOINTERFACE

        def AddRef(self, *args):
            return 1

        def Release(self, *args):
            return 0
    """)

    def __init__(self, indirname, iiddef, outfilename, dependances=()):
        self.indirname = indirname
        self.infilename = indirname
        self.outfilename = outfilename
        self.data = None
        self.dependances = dependances

        data = open(iiddef).read()
        self.iids_def = {}
        for line in data.split("\n"):
            name, iid = line.split("|")
            self.iids_def[name] = self.parse_iid(iid), iid

        self.exports = set([])
        self.imports = set([])

        self.parse()
        self.analyse(self.data)
        self.check_dependances()

    def parse(self):
        if self.data is not None:
            return self.data
        data = []
        for filename in glob.glob(self.indirname):
            print("Parsing <{0}>".format(filename))
            data.append(self.PARSER(open(filename).read()).parse())
        self.data = data
        return data

    def analyse(self, data):
        self.real_type = {}
        # self.add_exports("IID")
        # self.add_exports("GUID")
        # self.add_exports("LPGUID")  # setup in InitialCOMGenerator.HEADER
        # self.add_exports("REFGUID") # setup in InitialCOMGenerator.HEADER
        self.add_exports("COMInterface")
        self.add_exports("COMImplementation")
        for cominterface in data:
            #import pdb;pdb.set_trace()
            self.add_exports(cominterface.name)
            if cominterface.typedefptr:
                self.add_exports(cominterface.typedefptr)
        for cominterface in data:
            for method in cominterface.methods:
                self.add_imports(method.ret_type)
                for pos, arg in enumerate(method.args):
                    initial_arg = arg
                    if arg.type in self.exports or arg.type in self.IGNORE_INTERFACE:
                        # GUID type ?
                        if arg.type in ["GUID", "REFGUID", "LPGUID", "IID"]:
                            continue
                        # COM Interface ? -> PVOID !
                        atype = "PVOID"
                        byreflevel = arg.byreflevel - 1
                        method.args[pos] = arg = type(arg)(atype, byreflevel, arg.name)
                        self.real_type[arg] = initial_arg

                    elif arg.type == "void" and arg.byreflevel > 0:
                        # **void -> *PVOID
                        atype = "PVOID"
                        byreflevel = arg.byreflevel - 1
                        method.args[pos] = arg = type(arg)(atype, byreflevel, arg.name)
                        self.real_type[arg] = initial_arg
                    self.add_imports(arg.type)

    com_interface_comment_template = """ #{0} -> {1}"""
    com_interface_method_template = """ "{0}": ctypes.WINFUNCTYPE({1})({2}, "{0}"),"""
    com_interface_template = dedent("""
    class {0}(COMInterface):
        IID = generate_IID({2}, name="{0}", strid="{3}")

        _functions_ = {{
    {1}
        }}
    """)

    def generate(self):
        define = []
        for cominterface in self.data:
            methods_string = []
            for method_nb, method in enumerate(cominterface.methods):
                args_to_define = method.args[1:] #ctypes doesnt not need the This
                args_for_comment = [self.real_type.get(arg, arg) for arg in args_to_define]
                #import pdb;pdb.set_trace()
                str_args = []
                methods_string.append(self.com_interface_comment_template.format(method.name, ", ".join([arg.name +":"+ ("*"* arg.byreflevel) +arg.type for arg in args_for_comment])))
                for arg in args_to_define:
                    type = arg.type
                    for i in range(arg.byreflevel):
                        type = "POINTER({0})".format(type)
                    str_args.append(type)

                methods_string.append(self.com_interface_method_template.format(method.name, ", ".join([method.ret_type] + str_args), method_nb))
            #import pdb;pdb.set_trace()
            if cominterface.iid is not None:
                iid_str = cominterface.iid
                iid_python = self.parse_iid(iid_str)
            else:
                print("Lookup of IID for <{0}>".format(cominterface.name))
                iid_python, iid_str = self.iids_def[cominterface.name]
            define.append((self.com_interface_template.format(cominterface.name, "\n".join(methods_string), iid_python, iid_str)))

        deps = "\n".join(["from {0} import *".format(os.path.basename(dep.outfilename).rsplit(".")[0]) for dep in self.dependances])

        ctypes_code =  self.generate_import() + "\n" + self.HEADER + "\n".join(define)
        with open(self.outfilename, "w") as f:
            f.write(ctypes_code)
        print("<{0}> generated".format(self.outfilename))
        return ctypes_code

    def parse_iid(self, iid_str):
        part_iid = iid_str.split("-")
        str_iid = []
        str_iid.append("0x" + part_iid[0])
        str_iid.append("0x" + part_iid[1])
        str_iid.append("0x" + part_iid[2])
        str_iid.append("0x" + part_iid[3][:2])
        str_iid.append("0x" + part_iid[3][2:])
        for i in range(6): str_iid.append("0x" + part_iid[4][i * 2:(i + 1) * 2])
        return ", ".join(str_iid)



        com_interface_template = dedent("""
    class {0}(COMInterface):
        IID = generate_IID({2}, name="{0}", strid="{3}")

        _functions_ = {{
    {1}
        }}
    """)


class COMGenerator(InitialCOMGenerator):
    IMPORT_HEADER = "{deps}"
    HEADER = ""

class DefGenerator(InitialDefGenerator):
    IMPORT_HEADER = "{deps}"
    HEADER = ""

class MetafileGenerator(object):
    walker_generator = dedent("""
    def generate_walker(namelist, target_module):
        def my_walker():
            for name in namelist:
                yield name, getattr(target_module, name)
        return my_walker
    """)
    def __init__(self, filename):
        self.lol = {}
        self.filename = filename

    def add_exports(self, name, module, exports):
        self.lol[(name, module)] = exports

    def generate(self):
        with open(self.filename, "w") as f:
            # Generate lists
            for (name, module), exports in self.lol.items():
                f.write("{0} = {1}".format(name, exports))
                # f.write(str(y))
                f.write("\n")
            f.write(self.walker_generator)
            # Generate walkers
            for (name, module) in self.lol:
                f.write("import {0} as {0}_module\n".format(module))
                f.write("{0}_walker = generate_walker({0}, {1}_module)\n".format(name, module))


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
print(SCRIPT_DIR)
from_here = lambda path: pjoin(SCRIPT_DIR, path)


EXTENDED_STRUCT_FILE = glob.glob(pjoin(SCRIPT_DIR, "extended_structs", "*.py"))
EXTENDED_STRUCT = [os.path.basename(filename)[:-len(".py")] for filename in EXTENDED_STRUCT_FILE]

DEFAULT_INTERFACE_TO_IID = from_here("definitions\\interface_to_iid.txt")

# A partial define without the dependance to ntstatus defintion
# BOOTSTRAP!!
non_generated_def = InitialDefGenerator(from_here("definitions\\defines\\windef.txt"), from_here(r"..\windows\generated_def\\windef.py"))
ntstatus = NtStatusGenerator(from_here("definitions\\ntstatus.txt"), from_here(r"..\windows\generated_def\\ntstatus.py"), dependances=[non_generated_def])
# Not a real circular def (import not at the begin of file
defs_with_ntstatus = InitialDefGenerator(from_here("definitions\\defines\\*.txt"), from_here(r"..\windows\generated_def\\windef.py"), dependances=[ntstatus])

# YOLO HACK FOR NOW :DD
# import pdb;pdb.set_trace()


# for filename in [f for f in glob.glob(from_here("definitions\\defines\\*.txt")) if not f.endswith("\\windef.txt")]:
    # defs_with_ntstatus.append_input_file(from_here("definitions\\wintrust_crypt_def.txt"))
    # defs_with_ntstatus.append_input_file(from_here("definitions\\windef_error.txt"))
    # defs_with_ntstatus.append_input_file(from_here("definitions\\custom_rpc_windef.txt"))
    # defs_with_ntstatus.append_input_file(from_here("definitions\\windef_evtlog.txt"))
    # defs_with_ntstatus.append_input_file(filename)


structs = StructGenerator(from_here("definitions\\structures\\*.txt"), from_here(r"..\windows\generated_def\\winstructs.py"), dependances=[defs_with_ntstatus])

# for filename in [f for f in glob.glob(from_here("definitions\\structures\\*.txt")) if not f.endswith("\\winstruct.txt")]:
    # structs.append_input_file(filename)

# structs.append_input_file(from_here("definitions\\winstruct_apisetmap.txt"))
# structs.append_input_file(from_here("definitions\\display_struct.txt"))
# structs.append_input_file(from_here("definitions\\winstruct_bits.txt"))
# structs.append_input_file(from_here("definitions\\winstruct_alpc.txt"))
# structs.append_input_file(from_here("definitions\\winstruct_evtlog.txt"))
# structs.append_input_file(from_here("definitions\\winstruct_file_info.txt"))

functions = FuncGenerator(from_here("definitions\\functions\\*.txt"), from_here(r"..\windows\generated_def\\winfuncs.py"), dependances=[structs])

# for filename in [f for f in glob.glob(from_here("definitions\\functions\\*.txt")) if not f.endswith("\\winfunc.txt")]:
    # functions.append_input_file(filename)

# functions.append_input_file(from_here("definitions\\winfunc_crypto_wintrust.txt"))
# functions.append_input_file(from_here("definitions\\winfunc_notdoc.txt"))
# functions.append_input_file(from_here("definitions\\winfunc_evtlog.txt"))

com = InitialCOMGenerator(from_here("definitions\\com\\*.txt"), DEFAULT_INTERFACE_TO_IID, from_here(r"..\windows\generated_def\\interfaces.py"), dependances=[structs, defs_with_ntstatus])

# check for collision between ntstatus and defs_with_ntstatus

# Check for multiple define in defs_with_ntstatus
import collections

all_defs_names = [x.name for x in defs_with_ntstatus.parse()]

for name, nb in collections.Counter(all_defs_names).most_common():
    if nb > 1:
        print("Duplicated windef define: {0} ({1} defines)".format(name, nb))
    if nb == 1:
        break

all_ntstatus_names = [x[1] for x in ntstatus.parse()]

# Check for multiple define in ntstatus
for name, nb in collections.Counter(all_ntstatus_names).most_common():
    if nb > 1:
        print("Duplicated ntstatus define: {0} ({1} defines)".format(name, nb))
    if nb == 1:
        break

for collision_name in set(all_defs_names) & set(all_ntstatus_names):
    print("Duplicated ntstatus + windef define: {0}".format(collision_name))

meta = MetafileGenerator(from_here(r"..\windows\generated_def\\meta.py"))
meta.add_exports("windef", module="windef", exports=defs_with_ntstatus.exports - set(["Flag", "NATIVE_WORD_MAX_VALUE"]))
meta.add_exports("structs", module="winstructs", exports=structs.export_structs)
meta.add_exports("enums", module="winstructs", exports=structs.export_enums)
meta.add_exports("functions", module="winfuncs", exports=functions.exports)
meta.add_exports("interfaces", module="interfaces", exports=com.exports)


if __name__ == "__main__":
    ntstatus.generate()
    defs_with_ntstatus.generate()
    structs.generate()
    functions.generate()
    com.generate()
    print("Generating meta file")
    meta.generate()
    print("Generating documentation")
    ntstatus.generate_doc(from_here(r"..\docs\source\ntstatus_generated.rst"))
    defs_with_ntstatus.generate_doc(from_here(r"..\docs\source\windef_generated.rst"))
    structs.generate_doc(from_here(r"..\docs\source\winstructs_generated.rst"))

