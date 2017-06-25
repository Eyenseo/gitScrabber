name = "rdummy"
version = "1.0.0"


def rdummy(report, task_params, global_args):
    """
    Example report scrab task

    :param    report:       The report to analyse
    :param    task_params:  Parameter given explicitly for this task, for all
                            projects, defined in the task.yaml
    :param    global_args:  Arguments that will be passed to all tasks. They
                            _might_ contain something that is useful for the
                            task, but the task has to check if it is _there_ as
                            these are user provided. If they are needed to work
                            that check should happen in the argHandler.
    """
    report["report_exampe"] = "from: report_exampe"
