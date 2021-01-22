import inspect
from functools import wraps
from time import perf_counter
import sys


def get_caller(frame_stack):
    """Return caller of the frame_stack, frame_stack should be called by inspect.stack()[1][0]

    Args:
        frame_stack : inspect.stack()[1][0]

    Returns:
        Class: class instance of the caller
    """
    args, _, _, value_dict = inspect.getargvalues(frame_stack)
    # Check that the first paramater of the frame function is self
    if len(args) and args[0] == "self":
        # get self instance
        instance = value_dict.get("self", None)
        # return the class instance that called
        return instance
    return None


def set_object_by_caller(caller_type):
    stacks = inspect.stack()
    for stack in stacks:
        caller = get_caller(stack[0])
        if isinstance(caller, caller_type):
            return caller

    return None


def timer(func):
    @wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = perf_counter()
        value = func(*args, **kwargs)
        end_time = perf_counter()
        run_time = end_time - start_time
        print(f"{func.__name__!r}: {run_time:.4f} secs")
        return value
    return wrapper_timer


def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size
