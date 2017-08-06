from projectTaskRunner import ProjectTaskRunner
from reportTaskRunner import ReportTaskRunner
from utils import deep_merge, md5

from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os


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
    :param  max_workers:       The maximum workers to be used by the ThreadPool
    """

    def __init__(self, cache_dir, project_tasks, report_tasks, projects,
                 old_report, global_args, scrabTaskManager, max_workers=10):
        self.__cache_dir = cache_dir
        self.__project_tasks = project_tasks
        self.__report_tasks = report_tasks
        self.__projects = projects
        self.__old_report = old_report
        self.__global_args = global_args
        self.__scrabTaskManager = scrabTaskManager
        self.__max_workers = max_workers

        if self.__max_workers < 0:
            self.__max_workers = 1
        if self.__project_tasks is None:
            self.__project_tasks = []
        if self.__report_tasks is None:
            self.__report_tasks = []
        if not cache_dir.endswith('/'):
            self.__cache_dir += '/'

        self.__setup_tasks_configuration(self.__project_tasks)
        self.__setup_tasks_configuration(self.__report_tasks)
        self.__setup_project_data()

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

    def __setup_tasks_configuration(self, tasks):
        """
        Sets up the tasks configuration given from the user.

        Basically the configuration is streamlined and made more verbose to be
        used by the program without errors and checking at every use as the data
        structure 'defaults' are set here

        :param    tasks:  The tasks to set up the configuration for
        """
        for i, task in enumerate(tasks):
            if str is type(task):
                tasks[i] = {'name': task, 'parameter': {}}
            else:
                unpacked = self.__unpack_CommentedMap(task)

                if len(unpacked) != 2 or not isinstance(unpacked[1], dict):
                    raise Exception("The parameter for tasks have to be "
                                    "given in a map, but they weren't for "
                                    "the task '{}'".format(unpacked[0]))

                tasks[i] = {'name': unpacked[0]}
                tasks[i]['parameter'] = {}

                if unpacked[1] is not None:
                    tasks[i]['parameter'] = unpacked[1]

    def __setup_project_data(self):
        """
        Sets up the project specific data
        """
        for project in self.__projects:
            if 'location' not in project:
                project['location'] = self.__project_cache_dir(project)

            if 'git' in project:
                project['kind'] = 'git'
            elif 'archive' in project:
                project['kind'] = 'archive'
            else:
                project['kind'] = 'manual'

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
            scrabTask = self.__scrabTaskManager.get_task(task['name'])
            report[task_type][task['name']] = scrabTask['version']
        return report

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

    def __project_id(self, project):
        """
        Generates an unique id for the project. The id will be made up of the
        name of the project and the md5sum of the url or given id of the project

        :param    project:  The project to generate the id for

        :returns: An id for the given project
        """
        base_id = self.__project_name(project)

        hash_id = None
        if('git' in project):
            hash_id = md5(project['git'])
        elif('archive' in project):
            hash_id = md5(project['archive'])
        elif('id' in project):
            hash_id = md5(project['id'])
        else:
            raise Exception("The following project is neither an archive or "
                            "git and doesn't provide an id:\n"
                            "'{}'".format(project))

        return "{}_{}".format(base_id, hash_id)

    def __project_cache_dir(self, project):
        """
        Generates the path to the cache directory for the given project

        :param    project:  The project to generate the cache path for

        :returns: The path to the cache directory for the given project
        """
        return os.path.join(self.__cache_dir, self.__project_id(project))

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
        uid = self.__project_id(project)

        if self.__old_report and uid in self.__old_report:
            return self.__old_report[uid]
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
                            " something happened".format(
                                self.__project_name(project))
                            ).with_traceback(tb)

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
            if project['kind'] is not 'manual':
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
            uid = self.__project_id(project)
            result = self.__get_task_result(project, future)
            report = deep_merge(report, {'projects': {uid: result}})
            # TODO replace by logger or process indication
            i += 1
            print("~~ [{}/{}] Done with '{}' project tasks ~~".format(
                i, len(futures), self.__project_name(project)))
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
            if 'manual' in project:
                uid = self.__project_id(project)
                deep_merge(report, {'projects': {uid: project['manual']}})
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
