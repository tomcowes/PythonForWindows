import argparse

import pfw_windows
import pfw_windows.generated_def as gdef

def obj_with_link(obj):
    target = obj.target
    if target is None:
        return str(obj)
    return "{0} -> <{1}>".format(obj, target)

def fulllistdir(dir, depth=0):
    for name, obj in dir.items():
        print("{0} * {1}".format(" " * depth, obj_with_link(obj)))
        if obj.type == "Directory":
            try:
                fulllistdir(obj, depth + 4)
            except gdef.NtStatusException as e:
                print("{0} * {1}".format(" " * (depth + 4), e))


fulllistdir(pfw_windows.system.object_manager.root)