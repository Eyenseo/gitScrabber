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
                        "'{}' exited with return code: {} "
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


if __name__ == "__main__":
    print(run('ls', ['-al']))
    # print(run('false'))
