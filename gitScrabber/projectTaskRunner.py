from packaging import version
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
import os


class FileTaskRunner():
    """
    Helper class that is responsible for executing tasks that scrab at the
    files in a project. These tasks are meant to gather data, not necessarily
    interpret it. The interpretation is better left to the report scrab task.

    As we are IO-bound the scrab and merge methods of the FileTasks are called
    by multiple threads -- 5 per project.
    The Tasks are executed in parallel to prevent unnecessary reads.

    :param  project:           The project the scrab tasks run for
    :param  tasks:             The tasks that will run for the project
    :param  old_tasks:         The old tasks that were used to generate old_data
    :param  old_data:          The old data that was produced in a previous run
                               with old_tasks
    :param  global_args:       Arguments that will be passed to all tasks. They
                               _might_ contain something that is useful for the
                               task, but the task has to check if it is _there_
                               as these are user provided. If they are needed to
                               work that check should happen in the argHandler.
    :param  scrabTaskManager:  The ScrabTaskManager
    """

    def __init__(self, project, tasks, old_data,  old_tasks, global_args,
                 scrabTaskManager):
        self.__project = project
        self.__old_data = old_data
        self.__old_tasks = old_tasks
        self.__global_args = global_args
        self.__scrabTaskManager = scrabTaskManager
        # 5 workers per CPU core
        # we are IO-bound so five times CPU-cores processes is not too much
        self.__executor = ThreadPoolExecutor(max_workers=5)
        self.__tasks = self.__make_meta_tasks(tasks)
        self.__futures = {}
        self.__report = {}

    def __make_meta_tasks(self, tasks):
        """
        Creates meta tasks that will be executed for the project

        :param    tasks:  The tasks to consider -- these are mixed tasks and
                          only the 'file' tasks are needed, that have changed

        :returns: A dictionary where the key is the task to execute and value as
                  report that the task created
        """
        tasks_ = {}
        for task in tasks:
            meta_taks = self.__scrabTaskManager.get_task(task.name)

            if meta_taks.kind is not 'file':
                continue

            if self.__project.updated or self.__changed_task(meta_taks):
                scrab_task = meta_taks.construct(
                    parameter=task.parameter,
                    global_args=self.__global_args
                )
                tasks_[scrab_task] = {}
            elif self.__old_data and task.name in self.__old_data:
                self.__report[task.name] = self.__old_data[task.name]

        return tasks_

    def __read_file(self, filepath):
        """
        Reads a file by trying multiple encoding if necessary

        :param    filepath:  The file path to load the file from

        :returns: String containing the file contents
        """
        try:
            with open(filepath, 'r') as fd:
                return fd.read()
        except Exception as e:
            pass
        try:
            with open(filepath, mode='r', encoding="iso-8859-15") as fd:
                return fd.read()
        except Exception as e:
            pass
        raise Exception("Can't open file - tried encoding 'UTF-8' and "
                        "'iso-8859-15' on file {}".format(filepath))

    def __get_feature_result(self, path, future):
        """
        Gets the feature result.
        :param    path:    The path of the file that was analysed
        :param    future:  The future to get the result from

        :returns: The feature result.
        """
        try:
            return future.result()
        except Exception as e:
            tb = sys.exc_info()[2]
            raise Exception("While collecting the ScrabTask results for '{}'"
                            " something happened".format(path)
                            ).with_traceback(tb)

    def __changed_task(self, scrab_task):
        """
        Checks weather the scrab task has to be rerun based on an old report
        and the scab task versions

        :param    scrab_task:  The scrab task to check against

        :returns: True if the scrab task has to rerun False otherwise
        """
        return(
            not self.__old_tasks
            or scrab_task.name not in self.__old_tasks
            or version.parse(self.__old_tasks[scrab_task.name])
            != version.parse(scrab_task.version)
        )

    def __task_function_wrapper(self, filepath):
        """
        Wrapper function that executes __all__ tasks for the given file

        :param    filepath:  The filepath of the file that shall be analysed
        """
        file = self.__read_file(filepath)

        for task in self.__tasks:
            task.merge(self.__tasks[task], task.scrab(self.__project,
                                                      filepath,
                                                      file))

    def __queue_files(self):
        """
        Queues the project files into the ThreadPoolExecutor to be analysed for
        features
        """
        for dirpath, dirs, filenames in os.walk(self.__project.location,
                                                topdown=True):
            for d in dirs:  # ignore hidden / git directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                continue

            for file in filenames:
                if file[0] is '.':
                    # ignore hidden / git files
                    continue
                path = os.path.join(dirpath, file)
                feature = self.__executor.submit(
                    self.__task_function_wrapper, path)
                self.__futures[feature] = path

    def __wait_on_features(self):
        """
        Collects the feature results
        """
        for future in as_completed(self.__futures):
            project = self.__futures[future]
            self.__get_feature_result(project, future)

        for task in self.__tasks:
            self.__tasks[task] = task.finish(self.__tasks[task])

    def run_tasks(self):
        """
        Executes the FileTasks in a parallel fashion on all project files

        :returns: The report containing all task sub-reports of the project
                  information that were scrabbed together
        """
        self.__queue_files()
        self.__wait_on_features()

        for task in self.__tasks:
            self.__report[task.name] = self.__tasks[task]

        return self.__report


class ProjectTaskRunner:
    """
    The ProjectTaskRunner is responsible for executing tasks that scrab at the
    git repos and files. These tasks are meant to gather data, not necessarily
    interpret it. The interpretation is better left to the report scrab task.
    Each ProjectTaskRunner is responsible for a single project and will create
    the portion of the final report that contains the information of this
    project

    :param  project:           The project the scrab tasks run for
    :param  tasks:             The tasks that will run for the project
    :param  old_tasks:         The old tasks that were used to generate old_data
    :param  old_data:          The old data that was produced in a previous run
                               with old_tasks
    :param  global_args:       Arguments that will be passed to all tasks. They
                               _might_ contain something that is useful for the
                               task, but the task has to check if it is _there_
                               as these are user provided. If they are needed to
                               work that check should happen in the argHandler.
    :param  scrabTaskManager:  The ScrabTaskManager
    """

    def __init__(self, project, tasks, old_tasks, old_data, global_args,
                 scrabTaskManager):
        self.__project = project
        self.__tasks = tasks
        self.__old_tasks = old_tasks
        self.__old_data = old_data
        self.__global_args = global_args
        self.__scrabTaskManager = scrabTaskManager

    def __changed_task(self, scrab_task):
        """
        Checks weather the scrab task has to be rerun based on an old report
        and the scab task versions

        :param    scrab_task:  The scrab task to check against

        :returns: True if the scrab task has to rerun False otherwise
        """
        return(
            not self.__old_tasks
            or scrab_task.name not in self.__old_tasks
            or version.parse(self.__old_tasks[scrab_task.name])
            != version.parse(scrab_task.version)
        )

    def __run_git_tasks(self):
        """
        Runs the GitTasks by using the FileTaskRunner

        :returns: The sub-report containing all scrabbed information of this
                  project obtaind by the GitTasks
        """
        report = {}

        for task in self.__tasks:
            meta_task = self.__scrabTaskManager.get_task(task.name)

            if self.__project.kind is not 'git' or meta_task.kind is not 'git':
                continue

            if self.__project.updated or self.__changed_task(meta_task):
                scrab_task = meta_task.construct(
                    parameter=task.parameter,
                    global_args=self.__global_args)
                report[task.name] = scrab_task.scrab(self.__project)
            elif self.__old_data and task.name in self.__old_data:
                report[task.name] = self.__old_data[task.name]
        return report

    def __run_file_tasks(self):
        """
        Runs the FileTasks by using the FileTaskRunner

        :returns: The sub-report containing all scrabbed information of this
                  project obtaind by the FileTasks
        """
        f = FileTaskRunner(self.__project, self.__tasks,
                           self.__old_data, self.__old_tasks,
                           self.__global_args, self.__scrabTaskManager)
        return f.run_tasks()

    def run_tasks(self):
        """
        Runs GitTasks and FileTasks for the given project

        :returns: The sub-report containing all scrabbed information of this
                  project
        """
        report = self.__run_git_tasks()
        return {**report, **self.__run_file_tasks()}
