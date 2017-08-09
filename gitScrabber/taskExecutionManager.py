from projectTaskRunner import ProjectTaskRunner
from reportTaskRunner import ReportTaskRunner
from projectManager import GitProjectManager, ArchiveProjectManager

from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
from utils import deep_merge, md5

import sys
import os


class MetaProject():

    """
    Helper class that stores all information about the project

    :param    config:     The configuration from the tasks.yaml file
    :param    cache_dir:  The cache dir used by GitScrabber}
    """

    def __init__(self, config, cache_dir):
        self.name = self.__project_name(config)
        self.updated = True

        self.kind = None
        self.manual_data = None
        self.url = None

        if 'git' in config:
            self.kind = 'git'
            self.url = config['git']
        elif 'archive' in config:
            self.kind = 'archive'
            self.url = config['archive']
        elif 'manual' in config:
            self.kind = 'manual'
            self.manual_data = config['manual']
        else:
            raise Exception("The following project is neither an archive "
                            "or git and doesn't provide manual data:\n"
                            "'{}'".format(config))

        if self.url is None:
            self.id = "{}_{}".format(self.name, md5(self.name))
        else:
            self.id = "{}_{}".format(self.name, md5(self.url))

        if 'location' not in config:
            self.location = os.path.join(cache_dir, self.id)
        else:
            self.location = config['location']

    def __project_name(self, project):
        """
        Looks up the name of the project - either the last part of the url or a
        manually given id

        :param    project:  The project to look up the name for

        :returns: The name of the given project
        """
        if('id' in project):
            return project['id']
        elif('git' in project):
            return project['git'].rstrip('\\').rsplit('/', 1)[-1]
        elif('archive' in project):
            return project['archive'].rstrip('\\').rsplit('/', 1)[-1]
        else:
            raise Exception("The following project is neither an archive or "
                            "git and doesn't provide an id:\n"
                            "'{}'".format(project))


class MetaTask():

    """
    Helper class that stores all information that is needed to run the scrab
    tasks on the projects

    :param    config:  The configuration from the tasks.yaml file
    """

    def __init__(self, config):

        if str is type(config):
            self.name = config
            self.parameter = {}
        else:
            unpacked = self.__unpack_CommentedMap(config)

            if len(unpacked) != 2 or not isinstance(unpacked[1], dict):
                raise Exception("The parameter for tasks have to be "
                                "given in a map, but they weren't for "
                                "the task '{}'".format(unpacked[0]))

            self.name = unpacked[0]
            if unpacked[1] is None:
                self.parameter = {}
            else:
                self.parameter = unpacked[1]

    def __unpack_CommentedMap(self, yaml_dict):
        """
        Unpacks a CommentedMap from ruamel.yaml in a list

        :param    yaml_dict:  The yaml dictionary

        :returns: Array of the directory
        """
        l = []
        for x in yaml_dict.items():
            for y in x:
                l.append(y)
        return l


class TaskExecutionManager:
    """
    This class provides the means to execute the scrab tasks on projects and
    report.

    :param  cache_dir:         The cache dir to use for the downloaded code
    :param  project_tasks:     The tasks that will be executed on projects
    :param  report_tasks:      The tasks that will be executed on the projects
    :param  projects:          The projects the tasks will be executed for
    :param  old_report:        The previous report
    :param  global_args:       Arguments that will be passed to all tasks. They
                               _might_ contain something that is useful for the
                               task, but the task has to check if it is _there_
                               as these are user provided. If they are needed to
                               work that check should happen in the argHandler.
    :param  scrabTaskManager:  The ScrabTaskManager
    """

    def __init__(self, cache_dir, project_tasks, report_tasks, projects,
                 old_report, global_args, scrabTaskManager):
        self.__cache_dir = cache_dir
        self.__project_tasks = self.__setup_tasks_configuration(project_tasks)
        self.__report_tasks = self.__setup_tasks_configuration(report_tasks)
        self.__projects = self.__setup_project_data(projects)
        self.__old_report = old_report
        self.__global_args = global_args
        self.__scrabTaskManager = scrabTaskManager
        self.__max_workers = cpu_count()

        if not cache_dir.endswith('/'):
            self.__cache_dir += '/'

    def __setup_tasks_configuration(self, tasks):
        """
        Sets up the tasks configuration given from the user.

        Basically the configuration is streamlined and made more verbose to be
        used by the program without errors and checking at every use as the data
        structure 'defaults' are set here

        :param    tasks:  The tasks to set up the configuration for
        """
        if tasks is None:
            return []

        meta_tasks = []

        for task in tasks:
            meta_tasks.append(MetaTask(task))

        return meta_tasks

    def __setup_project_data(self, projects):
        """
        Sets up the project specific data
        """
        meta_projects = []

        for project in projects:
            meta_projects.append(MetaProject(project, self.__cache_dir))

        return meta_projects

    def __add_scrab_versions(self, task_type, tasks):
        """
        Adds the ScrabTask versions to the report

        :param    task_type:  The type of the loaded tasks, either 'archive',
                              'git' or 'report'
        :param    tasks:      The tasks to write the versions for in the report

        :returns: The report with the added information of the used tasks and
                  their versions
        """
        report = {task_type: {}}

        for task in tasks:
            scrabTask = self.__scrabTaskManager.get_task(task.name)
            report[task_type][task.name] = scrabTask.version

        return report

    def __extract_old_project_tasks(self):
        """
        Extracts the tasks form the previous / old report

        :returns: The tasks that were executed for the old report or None
        """
        if self.__old_report and 'project_tasks' in self.__old_report:
            return self.__old_report['project_tasks']
        return None

    def __extract_old_report_tasks(self):
        """
        Extracts the tasks form the previous / old report

        :returns: The tasks that were executed for the old report or None
        """
        if self.__old_report and 'report_tasks' in self.__old_report:
            return self.__old_report['report_tasks']
        return None

    def __extract_old_data(self, project):
        """
        Extracts the data generated in a previous / old run for a given project

        :param    project:  The project to extract the data for

        :returns: The data that was generated in a previous execution for the
                  given project
        """
        if self.__old_report and project.id in self.__old_report:
            return self.__old_report[project.id]
        return None

    def __get_task_result(self, project, future):
        """
        Gets the task result form a future

        :param    project:  The project to get the results for
        :param    future:   The future to get the results from

        :returns: The task result
        """
        try:
            return future.result()
        except Exception as e:
            tb = sys.exc_info()[2]
            raise Exception("While collecting the ScrabTask results for '{}'"
                            " something happened".format(project.name)
                            ).with_traceback(tb)

    def __update_project(self, project):
        """
        Updates the project - either cloning / pulling or re-/downloading it

        :returns: True if anything changed False if nothing changed
        """
        if project.kind == 'git':
            return GitProjectManager(project).update()
        elif project.kind == 'archive':
            return ArchiveProjectManager(project).update()
        else:
            # TODO handle manually downloaded archives
            pass

        return False

    def __project_task_wrapper(self, project, old_tasks, old_data):
        """
        Wraps the GitTaskRunner in a function call to be used by the
        ThreadPoolExecutor

        :param    project:    The project to run the scrab tasks for
        :param    old_tasks:  The old tasks that were run in a previous run -
                              used to decide if a task has to be rerun
        :param    old_data:   The old data that was generated with the old_tasks
                              in a previous run - used if the task doesn't have
                              to be rerun

        :returns: The subreport that contains all information generated by the
                  scrab tasks for the given project
        """
        project.updated = self.__update_project(project)
        runner = ProjectTaskRunner(project, self.__project_tasks,
                                   old_tasks, old_data,
                                   self.__global_args,
                                   self.__scrabTaskManager)
        return runner.run_tasks()

    def __queue_projects(self, executor):
        """
        Queues the projects of the given kind that shall be scrabbed for a given
        kind of task

        :param    executor:  The executor that will execute the functions
        :param    kind:      The kind of function that shall be run to scrab at
                             the projects

        :returns: A dict of futures that will contain the results of the
                  functions that where run for the projects
        """
        futures = {}
        old_tasks = self.__extract_old_project_tasks()

        for project in self.__projects:
            if project.kind is not 'manual':
                old_data = self.__extract_old_data(project)
                future = executor.submit(self.__project_task_wrapper, project,
                                         old_tasks, old_data)
                futures[future] = project
        return futures

    def __collect_project_results(self, report, futures):
        """
        Collects the results from the futures and merges into a single dict

        :param    report:   The new report so far
        :param    futures:  The futures to collect the results from

        :returns: The report for a collection of functions that where run for
                  projects
        """
        i = 0
        for future in as_completed(futures):
            project = futures[future]
            result = self.__get_task_result(project, future)
            report = deep_merge(report, {'projects': {project.id: result}})
            # TODO replace by logger or process indication
            i += 1
            print("~~ [{}/{}] Done with '{}' project tasks ~~".format(
                i, len(futures), project.name))
            # TODO write to report.part.yaml temporarily
        return report

    def __run_manual_task(self):
        """
        Writes the manually provided data for the projects in the report in a
        simultaneous fashion by using the ThreadPoolExecutor

        :returns: The report that contains all manually provided information of
                  the projects
        """
        report = {}
        for project in self.__projects:
            if project.manual_data is not None:
                deep_merge(report, {
                    'projects': {project.id: project.manual_data}})
        return report

    def __run_project_tasks(self):
        """
        Runs the project (archive and git) scrab tasks for the projects in
        parallel (sequentially for each project - the order is kept) by using
        the TheradPoolExecutor

        :returns: The report for all projects that contains the information
                  generated by the project (archive and git) scrab tasks
        """
        report = self.__add_scrab_versions('project_tasks',
                                           self.__project_tasks)
        executor = ThreadPoolExecutor(max_workers=self.__max_workers)
        futures = self.__queue_projects(executor)

        deep_merge(report, self.__collect_project_results(report, futures))
        return report

    def __run_report_tasks(self, report):
        """
        Runs the report scrab tasks over the report that contains all previously
        generated data.

        :param    report:  The report to run the report scrab tasks over

        :returns: The modified report
        """
        runner = ReportTaskRunner(
            self.__report_tasks, report, self.__global_args,
            self.__scrabTaskManager)
        runner.run_tasks()
        return deep_merge(report,
                          self.__add_scrab_versions('report_tasks',
                                                    self.__report_tasks))

    def __run_tasks(self):
        """
        Runs the manual data copying, git scrabber tasks, archive scrabber tasks
        and report scrabber tasks

        :returns: The complete report with all information that was requested
        """
        report = {}
        # TODO replace by logger or process indication
        print("~~ Starting manual task ~~")
        deep_merge(report, self.__run_manual_task())
        # TODO replace by logger or process indication
        print("~~ Starting project tasks ~~")
        deep_merge(report, self.__run_project_tasks(), overwrite=True)
        # TODO replace by logger or process indication
        print("~~ Starting report tasks ~~")
        return self.__run_report_tasks(report)

    def create_report(self):
        """
        Creates the report for the given tasks and projects from the constructor

        :returns: The complete report with all information that was requested
        """
        return self.__run_tasks()
