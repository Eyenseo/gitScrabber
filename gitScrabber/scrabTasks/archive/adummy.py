name = "adummy"
version = "1.0.0"


def adummy(report, project, task_params, global_args):
    """
    Dummy example - see authorContributerCounter for a better one

    :param    report:       The report
    :param    project:      The project
    :param    task_params:  Parameter given explicitly for this task, for all
                            projects, defined in the task.yaml
    :param    global_args:  Arguments that will be passed to all tasks. They
                            _might_ contain something that is useful for the
                            task, but the task has to check if it is _there_ as
                            these are user provided. If they are needed to work
                            that check should happen in the argHandler.
    """
    pass
    # return {}
