from ruamel.yaml.comments import CommentedMap

import hashlib
import os
import subprocess


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
    return out[0].decode(errors='ignore')


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
    new_env = dict(os.environ)  # Copy current environment
    new_env['LC_ALL'] = 'C'  # force English output for PISIX conform programs
    if(args is not None):
        process = subprocess.Popen(
            [program, *args], cwd=cwd, env=new_env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        process = subprocess.Popen(
            [program], cwd=cwd, env=new_env,
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


def sameStructure(d1, d2):
    """
    Checks weather the two directories have the same structure - only the values
    may be different but not the key

    To the structure does not count the type of the value

    Taken from https://stackoverflow.com/a/24193949/1935553

    :param    d1:   The first directory that will be compared with the second
    :param    d2:   The second directory that will be compared with the first

    :returns: True if the two directories have the same structure,
              False otherwise
    """
    if isinstance(d1, dict):
        if isinstance(d2, dict):
            # then we have shapes to check
            return (d1.keys() == d2.keys() and
                    # so the keys are all the same
                    all(sameStructure(d1[k], d2[k]) for k in d1.keys()))
            # thus all values will be tested in the same way.
        else:
            return False  # d1 is a dict, but d2 isn't
    else:
        return not isinstance(d2, dict)  # if d2 is a dict, False, else True.


def containedStructure(containee, container):
    """
    Checks weather the structure of the given containee is contained in the
    given container. This is similar to sameStructure with the difference that
    only a subset has to be matching.

    To the structure counts the type of the value except None which matches all
    Types

    :param    containee:  The containee which structure  has to be contained in
                          the container.
    :param    container:  The container that has to contain the structure of the
                          containee

    :returns: True if the structure of the containee is contained in the
              container,
              False otherwise
    """

    if isinstance(containee, dict):
        if isinstance(container, dict):
            # then we have shapes to check
            return (set(containee.keys()).issubset(set(container.keys())) and
                    # so the keys are all the same
                    all(containedStructure(containee[k], container[k])
                        for k in containee.keys()))
            # thus all values will be tested in the same way.
        else:
            return False  # containee is a dict, but container isn't
    elif isinstance(containee, list):
        if isinstance(container, list):
            return set(containee).issubset(set(container))
        else:
            return False   # containee is a lit, but container isn't
    elif containee is None:
        return True
    else:
        # else they have to be the same type
        return isinstance(container, type(containee))


def to_dict(dict_like):
    """
    Converts an object that inherits from dictionary to a plain dictionary.
    This is useful for CommentedMap objects.

    :param    dict_like:  The dictionary like object

    :returns: A plain dictionary
    """
    d = dict(dict_like)

    for key in d:
        if isinstance(d[key], dict):
            d[key] = to_dict(d[key])
    return d


if __name__ == "__main__":
    print(run('ls', ['-al']))
    # print(run('false'))
