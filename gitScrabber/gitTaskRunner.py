from packaging import version
import utils
import os


class GitTaskRunner:
    """
    The GitTaskRunner is responsible for executing tasks that scrab at a git
    repo

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

    def __init__(self, project, tasks, old_tasks, old_data,
                 global_args, scrabTaskManager):
        self.__project = project
        self.__tasks = tasks
        self.__old_tasks = old_tasks
        self.__old_data = old_data
        self.__global_args = global_args
        self.__scrabTaskManager = scrabTaskManager

    def __validate_repo_folder(self):
        """
        Checks weather the repo folder of the project is indeed a git repo or a
        used folder

        :returns: True if it is a git repo folder False if the folder does not
                  exist

        :exception Exception:  If the folder exists and isn't a git repo
        """
        cache_dir = self.__project['location']

        if os.path.isdir(cache_dir + '/.git'):
            try:
                utils.run(program='git', args=['status'], cwd=cache_dir)
            except Exception as e:
                raise Exception(
                    "The git repo '{}' seems to be corrupt "
                    "- please delete it.".format(cache_dir))
            return True
        else:
            if os.path.isdir(cache_dir):
                raise Exception("The directory '{}' is used and would be "
                                "overwritten when cloning.".format(cache_dir))
            else:
                return False

    def __update_repo(self):
        """
        Updates the git repo - either cloning it for the first time or pulling
        changes

        :returns: True if anything changed False if nothing changed
        """

        cache_dir = self.__project['location']
        url = self.__project['git']

        if(self.__validate_repo_folder()):
            result = utils.run(program='git', args=['pull', ], cwd=cache_dir)
            if 'Already up-to-date' in result:
                return False
        else:
            utils.run(program='git', args=['clone', url, cache_dir])
        return True

    def __changed_task(self, scrabTask):
        """
        Checks weather the scrab task has to be rerun based on an old report
        and the scab task versions

        :param    scrabTask:  The scrab task to check against

        :returns: True if the scrab task has to rerun False otherwise
        """
        return(
            not self.__old_tasks
            or scrabTask['name'] not in self.__old_tasks
            or version.parse(self.__old_tasks[scrabTask['name']])
            != version.parse(scrabTask['version'])
        )

    def run_tasks(self):
        """
        This function is responsible to ensure that the git repo is present. It
        also decides weather the scrab task has to run again based in its
        version and the version mentioned in the old report as well as if the
        git repo had file changes

        :returns: The sub-report containing all results of the scrab tasks that
                  ran for this project
        """
        report = {}
        updated = self.__update_repo()

        for task in self.__tasks:
            scrabTask = self.__scrabTaskManager.get_task(task['name'])

            if(updated or self.__changed_task(scrabTask)):
                task_report = scrabTask['function'](report,
                                                    self.__project,
                                                    task['parameter'],
                                                    self.__global_args)
                report[task['name']] = task_report
            elif task['name'] in self.__old_data:
                report[task['name']] = self.__old_data[task['name']]

        return report
