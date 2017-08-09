from ..scrabTask import GitTask

import utils

name = "ProjectDates"
version = "1.1.0"


class ProjectDates(GitTask):
    """
    Gets the first and last commit date in ISO format

    Example:
        ProjectDates:
          first_change: '1998-12-21T10:52:45+00:00'
          last_change: '2017-08-09T13:37:06+10:00'

    :param  parameter:    Parameter given explicitly for this task, for all
                          projects, defined in the task.yaml
    :param  global_args:  Arguments that will be passed to all tasks. They
                          _might_ contain something that is useful for the task,
                          but the task has to check if it is _there_ as these
                          are user provided. If they are needed to work that
                          check should happen in the argHandler.
    """

    def __init__(self, parameter, global_args):
        super(ProjectDates, self).__init__(name, version, parameter,
                                           global_args)
        self.__project = None

    def __first_commit_date(self):
        """
        The function will obtain the first commit date from the project
        repository

        :returns: The date of the first commit in the projects repository
                  (2005-04-16T15:20:36-07:00)
        """
        return utils.run('git',
                         ['log', '--all', '--format=%cI', '--first-parent',
                             '--reverse', '--max-parents=0'],
                         self.__project.location).splitlines()[0].rstrip()

    def __last_commit_date(self):
        """
        The function will obtain the last commit date from the project
        repository

        :returns: The date of the last commit in the projects repository
                  (2017-08-03T15:25:14-07:00)
        """
        return utils.run('git', ['log', '--all', '-1', '--format=%cI'],
                         self.__project.location).rstrip()

    def scrab(self, project):
        """
        Gets the first and last commit date in ISO format

        :param    project:  The project

        :returns: The first and last commit date in ISO format
                  Example:
                      ProjectDates:
                        first_change: '1998-12-21T10:52:45+00:00'
                        last_change: '2017-08-09T13:37:06+10:00'
        """
        self.__project = project
        report = {}
        report['first_change'] = self.__first_commit_date()
        report['last_change'] = self.__last_commit_date()
        return report
