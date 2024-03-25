import pfw_windows
import pfw_windows.test

p = pfw_windows.test.pop_proc_32()
print("Child is {0}".format(p))

PIPE_NAME = "PFW_Pipe"

rcode = """
import pfw_windows

f = open('tst.txt', "w+")
fh = pfw_windows.utils.get_handle_from_file(f)
hm = pfw_windows.winproxy.CreateFileMappingA(fh, dwMaximumSizeLow=0x1000, lpName=None)
addr = pfw_windows.winproxy.MapViewOfFile(hm, dwNumberOfBytesToMap=0x1000)

pfw_windows.pipe.send_object("{pipe}", addr)
"""

with pfw_windows.pipe.create(PIPE_NAME) as np:
    print("Created pipe is {0}".format(np))
    p.execute_python(rcode.format(pipe=PIPE_NAME))
    print("Receiving object from injected process")
    addr = np.recv()

print("Remote Address = {0:#x}".format(addr))
print("Querying memory in target at <{0:#x}>".format(addr))
print("    * {0}".format(p.query_memory(addr)))
print("Querying mapped file in target at <{0:#x}>".format(addr))
print("    * {0}".format(p.get_mapped_filename(addr)))
p.exit()