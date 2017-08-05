import utils

name = "project_dates"
version = "1.0.0"


def __first_commit_date(project):
    """
    The function will obtain the first commit date from the project repository

    :param    project:  The project to get the first commit date from

    :returns: The date of the first commit in the projects repository
              (2005-04-16T15:20:36-07:00)
    """
    return utils.run('git',
                     ['log', '--all', '--format=%cI', '--first-parent',
                         '--reverse', '--max-parents=0'],
                     project['location']).rstrip()


def __last_commit_date(project):
    """
    The function will obtain the last commit date from the project repository

    :param    project:  The project to get the last commit date from

    :returns: The date of the last commit in the projects repository
              (2017-08-03T15:25:14-07:00)
    """
    return utils.run('git', ['log', '--all', '-1', '--format=%cI'],
                     project['location']).rstrip()


def project_dates(project_report, project, task_params,  global_args):
    """
    Gets the first and last commit date in ISO format

    :param    project_report:  The project report so far - __DO NOT MODIFY__
    :param    project:         The project
    :param    task_params:     Parameter given explicitly for this task, for all
                               projects, defined in the task.yaml
    :param    global_args:     Arguments that will be passed to all tasks. They
                               _might_ contain something that is useful for the
                               task, but the task has to check if it is _there_
                               as these are user provided. If they are needed to
                               work that check should happen in the argHandler.

    :returns: The report of this task as a dictionary
    """
    report = {}
    report['first_change'] = __first_commit_date(project)
    report['last_change'] = __last_commit_date(project)
    return report
