import inspect


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
