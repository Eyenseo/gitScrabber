import subprocess
import hashlib


def __validate_exec_args(program, args):
    """
    Validates the types of the program and arguments that will be executed

    :param    program:  The program
    :param    args:     The arguments
    """
    if type(program) is not str:
        raise Exception("The program has to given as a string")
    if args is not None:
        if type(args) is not list:
            raise Exception("The arguments for the program '{}' have "
                            "to be given as a list of strings".format(
                                program))
        else:
            for x in args:
                if type(x) is not str:
                    raise Exception("The arguments for the program '{}' have "
                                    "to be given as a list of strings".format(
                                        program))


def __handle_result(process):
    """
    handels the results from the executed program

    :param    process:  The process

    :returns: the data from stdout of the program
    """
    out = process.communicate()
    if process.returncode is not 0:
        raise Exception("When executing "
                        "'{}' exited with return code: '{}' "
                        " and message:\n{}".format(
                            process.args, process.returncode, out[1].decode()))
    return out[0].decode()


def run(program, args=[], cwd=None):
    """
    Executes a given program with given arguments in a specific dir

    :param    program:  The program
    :param    args:     The arguments
    :param    cwd:      The working directory for the program

    :returns: the data from stdout of the program
    """
    __validate_exec_args(program, args)
    process = None
    if(args is not None):
        process = subprocess.Popen(
            [program, *args], cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        process = subprocess.Popen(
            [program], cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return __handle_result(process)


def deep_merge(a, b, overwrite=False, path=None):
    """
    Deep merges dict b in dict a

    Taken from https://stackoverflow.com/a/7205107/1935553

    :param    a:          dict to merged into
    :param    b:          dict to merge
    :param    overwrite:  If true values from a will be overwritten by values
                          from b that share the same key in the same level
    :param    path:       The path - needed for error reporting

    :returns: deep merged dict (a)
    """
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                deep_merge(a[key], b[key], overwrite, path + [str(key)])
            elif not overwrite or a[key] == b[key]:
                pass  # same leaf value
            elif overwrite:
                a[key] = b[key]
            else:
                raise Exception("Conflict at '{}'.".format(path + [str(key)]))
        else:
            a[key] = b[key]
    return a


def md5(string):
    """
     Calculates a MD% sum of the provided string

     :param    string:  The string to calculate teh MD% sum

     :returns: MD% sum of the provided string
     """
    return hashlib.md5(string.encode('utf-8')).hexdigest()


if __name__ == "__main__":
    print(run('ls', ['-al']))
    # print(run('false'))
