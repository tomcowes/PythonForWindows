import pfw_windows.test

p = pfw_windows.test.pop_proc_32()
print("Child is {0}".format(p))

PIPE_NAME = "PFW_Pipe"

lower_integrity = """
import pfw_windows
pfw_windows.current_process.token.integrity = 0x1000
"""

p.execute_python(lower_integrity)
assert p.token.integrity == 0x1000

send_object = """
pfw_windows.pipe.send_object("{pipe}", {{"KIKOU": "LOL"}})
""".format(pipe=PIPE_NAME)

# S:(ML;;;;;LW) -> Allow connection from LOW integrity
with pfw_windows.pipe.create(PIPE_NAME, security_descriptor="S:(ML;;;;;LW)") as np:
    print("Created pipe is {0}".format(np))
    p.execute_python(send_object)
    print("Receiving object from injected process")
    obj = np.recv()
    print("obj = {0}".format(obj))