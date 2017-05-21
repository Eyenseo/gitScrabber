import subprocess


def __validate_exec_args(program, args):
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
    out = process.communicate()
    if process.returncode is not 0:
        raise Exception("When executing "
                        "'{}' exited with return code: {} "
                        " and message:\n{}".format(
                            process.args, process.returncode, out[1].decode()))
    return out[0].decode()


def run(program, args=[], cwd=None):
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
