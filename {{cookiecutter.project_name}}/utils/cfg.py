import os


def to_bool(value):
    true_list = ["1", 1, "on", "yes", "true", "True", "open"]
    if value in true_list:
        return True
    return False


def cfg(prefix, key=None, is_bool=False, is_int=False, is_float=False, is_eval=False):
    env = f"{prefix.upper()}_{key.upper()}" if key else f"{prefix.upper()}"
    result = os.getenv(env)
    if is_bool:
        return to_bool(result)
    elif is_int:
        return int(result)
    elif is_float:
        return float(result)
    elif is_eval:
        return eval(result)
    else:
        return result
