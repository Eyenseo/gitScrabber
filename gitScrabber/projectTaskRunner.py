from utils import md5

from packaging import version
from concurrent.futures import ThreadPoolExecutor, as_completed

import os
import regex


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
        self.__futures = {}
        self.__report = {}
        self.__tasks = self.__make_meta_tasks(tasks)

    def __make_meta_tasks(self, tasks):
        """
        Creates meta tasks that will be executed for the project

        :param    tasks:  The tasks to consider -- these are mixed tasks and
                          only the 'file' tasks are needed, that have changed

        :returns: A dictionary where the key is the task to execute and value as
                  report that the task created
        """
        tasks_ = {}
        for meta_task in tasks:
            task_wrapper = self.__scrabTaskManager.get_task(meta_task.name)

            if task_wrapper.kind is not 'file':
                continue

            if (self.__project.updated
                    or self.__changed_task(task_wrapper, meta_task)):
                scrab_task = task_wrapper.construct(
                    parameter=meta_task.parameter,
                    global_args=self.__global_args
                )
                tasks_[scrab_task.name] = scrab_task
            elif self.__old_data and meta_task.name in self.__old_data:
                self.__report[meta_task.name] = self.__old_data[meta_task.name]
        return tasks_

    def __is_binary(self, filename):
        """
        { function_description }

        :param    filename:  The filename

        :returns: { description_of_the_return_value }
        """
        header = open(filename, 'rb').read(512)  # read 512 bytes
        if not header:
            return True  # Empty is considered a binary file
        # Count 'human' text characters
        text = regex.findall(rb"[\w\t \(\)\.=!'\+\-\*\\]", header)

        if float(len(text)) / float(len(header)) < 0.80:
            return True
        return False

    def __read_file(self, filepath):
        """
        Reads a file by trying multiple encoding if necessary

        :param    filepath:  The file path to load the file from

        :returns: String containing the file contents
        """
        try:
            with open(filepath, mode='r') as fd:
                return fd.read()
        except Exception as e:
            pass
        try:
            with open(filepath, mode='r', encoding="iso-8859-15") as fd:
                return fd.read()
        except Exception as e:
            pass

        if self.__is_binary(filepath):
            with open(filepath, mode='rb') as fd:
                return fd.read().decode(encoding='ascii', errors='ignore')
        else:
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
            raise Exception("While collecting the ScrabTask results for '{}'"
                            " something happened".format(path)
                            ) from e

    def __changed_task(self, task_wrapper, meta_task):
        """
        Checks weather the scrab task has to be rerun based on an old report
        and the scab task versions

        :param    task_wrapper:  The scrab task to check against
        :param    meta_task:     The meta task that contains the parameter for
                                 the scrab task

        :returns: True if the scrab task has to rerun False otherwise
        """
        return(
            not self.__old_tasks
            or task_wrapper.name not in self.__old_tasks
            or version.parse(self.__old_tasks[task_wrapper.name]['version'])
            != version.parse(task_wrapper.version)
            or self.__old_tasks[task_wrapper.name]['parameter']
            != md5(str(meta_task.parameter))
        )

    def __task_function_wrapper(self, filepath):
        """
        Wrapper function that executes __all__ tasks for the given file

        :param    filepath:  The filepath of the file that shall be analysed
        """
        file = self.__read_file(filepath)
        reports = {}

        for task_name in self.__tasks:
            reports[task_name] = self.__tasks[task_name].scrab(
                self.__project, filepath, file)
        return reports

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
                if os.path.isfile(path):
                    feature = self.__executor.submit(
                        self.__task_function_wrapper, path)
                    self.__futures[feature] = path

    def __collect_feature_results(self):
        """
        Collects the feature results
        """
        for future in as_completed(self.__futures):
            project = self.__futures[future]
            reports = self.__get_feature_result(project, future)

            for task_name in reports:
                if len(reports[task_name]) > 0:
                    if task_name not in self.__report:
                        self.__report[task_name] = reports[task_name]
                    else:
                        task = self.__tasks[task_name]
                        report = self.__report[task_name]
                        report = task.merge(report, reports[task_name])

        for task_name in self.__tasks:
            if task_name in self.__report:
                self.__report[task_name] = self.__tasks[
                    task_name].finish(self.__report[task_name])

    def run_tasks(self):
        """
        Executes the FileTasks in a parallel fashion on all project files

        :returns: The report containing all task sub-reports of the project
                  information that were scrabbed together
        """
        self.__queue_files()
        self.__collect_feature_results()

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

    def __changed_task(self, task_wrapper, meta_task):
        """
        Checks weather the scrab task has to be rerun based on an old report
        and the scab task versions

        :param    task_wrapper:  The scrab task to check against
        :param    meta_task:     The meta task that contains the parameter for
                                 the scrab task

        :returns: True if the scrab task has to rerun False otherwise
        """
        return(
            not self.__old_tasks
            or task_wrapper.name not in self.__old_tasks
            or version.parse(self.__old_tasks[task_wrapper.name]['version'])
            != version.parse(task_wrapper.version)
            or self.__old_tasks[task_wrapper.name]['parameter']
            != md5(str(meta_task.parameter))
        )

    def __run_git_tasks(self):
        """
        Runs the GitTasks by using the FileTaskRunner

        :returns: The sub-report containing all scrabbed information of this
                  project obtaind by the GitTasks
        """
        report = {}

        for meta_task in self.__tasks:
            task_wrapper = self.__scrabTaskManager.get_task(meta_task.name)

            if ((self.__project.kind is not 'git'
                 and self.__project.kind is not 'svn')
                    or task_wrapper.kind is not 'git'):
                continue

            if (self.__project.updated
                    or self.__changed_task(task_wrapper, meta_task)):
                scrab_task = task_wrapper.construct(
                    parameter=meta_task.parameter,
                    global_args=self.__global_args)

                sub_report = scrab_task.scrab(self.__project)
                if sub_report and len(sub_report) > 0:
                    report[meta_task.name] = sub_report
            elif self.__old_data and meta_task.name in self.__old_data:
                report[meta_task.name] = self.__old_data[meta_task.name]
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
