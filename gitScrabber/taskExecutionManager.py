from gitTaskRunner import GitTaskRunner
from archiveTaskRunner import ArchiveTaskRunner
from reportTaskRunner import ReportTaskRunner
from utils import deep_merge, md5

from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os


class TaskExecutionManager:
    """
    Class for task execution manager.

    :param    cache_dir:         The cache dir to use for the downloaded
                                 code
    :param    tasks:             The tasks that will be executed for the
                                 projects
    :param    projects:          The projects the tasks will be executed for
    :param    previous_report:   The previous report
    :param    global_args:       Arguments that will be passed to all tasks.
                                 They _might_ contain something that is useful
                                 for the task, but the task has to check if it
                                 is _there_ as these are user provided. If they
                                 are needed to work that check should happen in
                                 the argHandler.
    :param    scrabTaskManager:  The ScrabTaskManager
    :param    max_workers:       The maximum workers to be used by the
                                 ThreadPool
    """

    def __init__(self, cache_dir, tasks, projects, previous_report,
                 global_args, scrabTaskManager, max_workers=10):
        self.__cache_dir = cache_dir
        self.__tasks = tasks
        self.__projects = projects
        self.__previous_report = previous_report
        self.__global_args = global_args
        self.__scrabTaskManager = scrabTaskManager
        self.__max_workers = max_workers if max_workers > 0 else 1

        self.__task_wrapper = {
            'archive': self.__archive_task_wrapper,
            'git': self.__git_task_wrapper,
            'manual': self.__manual_task_wrapper,
        }
        self.__kind_mapper = {
            'archive': ['archive', 'git'],
            'git': ['git'],
            'manual': ['archive', 'git', 'manual'],
        }

        if(not cache_dir.endswith('/')):
            self.__cache_dir += '/'

        for project in self.__projects:
            if 'location' not in project:
                project['location'] = self.__project_cache_dir(project)

    def __add_scrab_versions(self, kind):
        """
        Adds the ScrabTask versions to the report

        :param    kind:  The kind of scrabber to add

        :returns: The report with the added information of the used tasks and
                  their versions
        """
        report = {'tasks': {}}
        for task in self.__tasks[kind]:
            scrabTask = self.__scrabTaskManager.get_task(task)
            report['tasks'][task] = scrabTask['version']
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

    def __extract_tasks(self):
        """
        Extracts the tasks form the previous report

        :returns: The tasks that were executed for the old report or None
        """
        if self.__previous_report and 'tasks' in self.__previous_report:
            return self.__previous_report['tasks']
        return None

    def __extract_data(self, project):
        """
        Extracts the data generated in a previous run for a given project

        :param    project:  The project to extract the data for

        :returns: The data that was generated in a previous execution for the
                  given project
        """
        uid = self.__project_id(project)

        if self.__previous_report and uid in self.__previous_report:
            return self.__previous_report[uid]
        return None

    def __queue_projects(self, executor, kind):
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
        task_wrapper = self.__task_wrapper[kind]
        old_tasks = self.__extract_tasks()

        for project in self.__projects:
            if any(x in self.__kind_mapper[kind] for x in project):
                old_data = self.__extract_data(project)
                future = executor.submit(task_wrapper, project,
                                         old_tasks, old_data)
                futures[future] = project
        return futures

    def __collect_task_results(self, futures):
        """
        Collects the results from the futures and merges into a single dict

        :param    futures:  The futures to collect the results from

        :returns: The report for a collection of functions that where run for
                  projects
        """
        report = {}
        for future in as_completed(futures):
            project = futures[future]
            uid = self.__project_id(project)
            result = self.__get_task_result(project, future)
            report = deep_merge(report, {'projects': {uid: result}})
        return report

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
            raise Exception("While working on the git "
                            "ScrabTasks for '{}' something happened".format(
                                self.__project_name(project))
                            ).with_traceback(tb)

    def __multithreaded_tasks(self, kind):
        """
        Executes a given kind of function for the projects of that kind
        simultaneously by using a ThreadPool

        :param    kind:  The kind of functions to run for the projects

        :returns: The report for the given kind of functions that contains the
                  information generated by the scrabTasks
        """
        executor = ThreadPoolExecutor(max_workers=self.__max_workers)
        futures = self.__queue_projects(executor, kind)
        return self.__collect_task_results(futures)

    def __archive_task_wrapper(self, project, old_tasks, old_data):
        runner = ArchiveTaskRunner(project, self.__tasks['archive'],
                                   old_tasks, old_data,
                                   self.__global_args,
                                   self.__scrabTaskManager)
        return runner.run_tasks()

    def __run_archive_tasks(self):
        report = self.__multithreaded_tasks('archive')
        report = {**report, **self.__add_scrab_versions('archive')}
        return report

    def __git_task_wrapper(self, project, old_tasks, old_data):
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
        runner = GitTaskRunner(project, self.__tasks['git'],
                               old_tasks, old_data, self.__global_args,
                               self.__scrabTaskManager)
        return runner.run_tasks()

    def __run_git_tasks(self):
        """
        Runs the git scrab tasks for the projects simultaneously by using the
        TheradPoolExecutor

        :returns: The report for all git projects that contains the information
                  generated by the git scrab tasks
        """
        report = self.__multithreaded_tasks('git')
        report = {**report, **self.__add_scrab_versions('git')}
        return report

    def __manual_task_wrapper(self, project, old_tasks, old_data):
        """
        Inserts the manually provided information in the report for all projects
        that have such information.

        The information _will_ be overwritten by later executed tasks. This
        should not be a problem as manually provided information should only be
        necessary for non generateable information.

        :param    project:    The project to write the manually provided
                              information for in the report
        :param    old_tasks:  __unused__
        :param    old_data:   __unused__

        :returns: { description_of_the_return_value }
        """
        if 'manual' in project:
            return project['manual']
        return {}

    def __run_manual_tasks(self):
        """
        Writes the manually provided data for the projects in the report in a
        simultaneous fashion by using the ThreadPoolExecutor

        :returns: The report that contains all manually provided information of
                  the projects
        """
        return self.__multithreaded_tasks('manual')

    def __run_report_tasks(self, report):
        """
        Runs the report scrab tasks over the report that contains all previously
        generated data.

        :param    report:  The report to run the report scrab tasks over

        :returns: The modified report
        """
        runner = ReportTaskRunner(
            self.__tasks['report'], report, self.__global_args,
            self.__scrabTaskManager)
        runner.run_tasks()
        return deep_merge(report, self.__add_scrab_versions('report'))

    def __run_tasks(self):
        """
        Runs the manual data copying, git scrabber tasks, archive scrabber tasks
        and report scrabber tasks

        :returns: The complete report with all information that was requested
        """
        report = {}
        deep_merge(report, self.__run_manual_tasks())
        deep_merge(report, self.__run_git_tasks(), overwrite=True)
        deep_merge(report, self.__run_archive_tasks())
        return self.__run_report_tasks(report)

    def create_report(self):
        """
        Creates the report for the given tasks and projects from the constructor

        :returns: The complete report with all information that was requested
        """
        return self.__run_tasks()
