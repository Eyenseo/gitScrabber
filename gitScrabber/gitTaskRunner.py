from concurrent.futures import ThreadPoolExecutor, as_completed
from packaging import version
import utils
import sys
import os


class GitTaskRunner:

    """
    The GitTaskRunner executes the scrab tasks specified in the task.yaml file

    :param  task_yaml:         The task configuration
    :param  old_report:        The old report
    :param  scrabTaskManager:  The scrab task manager
    :param  git_dir:           The git dir
    """

    def __init__(self, task_yaml, old_report, scrabTaskManager, git_dir):

        super(GitTaskRunner, self).__init__()
        self.max_workers = 10
        self.task_yaml = task_yaml
        self.old_report = old_report
        self.scrabTaskManager = scrabTaskManager
        self.git_dir = git_dir
        if(not git_dir.endswith('/')):
            self.git_dir += '/'

    def __git_tasks(self, project):
        '''
        The git task wrapper

        This function is responsible to ensure that the git repo is present - if
        it is a git scrab task. It also decides weather the scrab task has to
        run again based in its version and the version mentioned in the old
        report as well as if the git repo had file changes

        :param    project:  The project

        :returns: The sub-report containing all results of the scrab tasks that
                  ran for this project
        '''

        report = {}
        updated = True

        if('data' not in project):
            updated = self.__update_repo(self.git_dir, project['url'])
            project['location'] = self.__get_repo_path(
                self.git_dir, project['url'])

        for task_name in self.task_yaml['tasks']['git']:
            scrabTask = self.scrabTaskManager.get_task(task_name)

            if(updated or self.__changed_task(scrabTask)):
                task_report = {}
                scrabTask['function'](task_report, project)
                report[scrabTask['name']] = task_report
            else:
                report[scrabTask['name']] = self.old_report[
                    'projects'][project['url']][scrabTask['name']]

        return report

    def __get_repo_path(self, cwd, url):
        """
        Gets the path for the git repos.

        :param    cwd:  The base path / 'working directory'
        :param    url:  The url to the git

        :returns: The git path
        """
        return cwd + '/' + url.rsplit('/', 1)[-1]

    def __check_repo_folder(self, repo):
        """
        Checks weather the given repo folder is indeed a repo or a used folder

        :param    repo:  The repo path to check

        :returns: True if it is a git repo folder False if the folder does not
                  exist

        :exception Exception:  If the folder exists and isn't git git
        """
        if os.path.isdir(repo + '/.git'):
            try:
                utils.run(program='git', args=['status'], cwd=repo)
            except Exception as e:
                raise Exception(
                    "The git repo '{}' seems to be corrupt "
                    "- please delete it.".format(repo))
            return True
        else:
            if os.path.isdir(repo):
                raise Exception("The directory '{}' is used and would be "
                                "overwritten when cloning.".format(repo))
            else:
                return False

    def __update_repo(self, cwd, url):
        """
        Updates the git repo - either cloning it for the first time or pulling
        changes

        :param    cwd:   The 'working directory' for the git command
        :param    url:   The url to the git repo

        :returns: True if anything changed False if nothing changed
        """
        repo_location = self.__get_repo_path(cwd, url)

        if(self.__check_repo_folder(repo_location)):
            result = utils.run(program='git', args=['pull'], cwd=repo_location)
            if 'Already up-to-date' in result:
                return False
        else:
            utils.run(program='git', args=['clone', url], cwd=cwd)
        return True

    def __changed_task(self, scrabTask):
        """
        Checks weather the scrab task has to be re run based on an old report
        and the scab task versions

        :param    scrabTask:  The scrab task to check against

        :returns: True if the scrab task has to rerun False otherwise
        """
        return(
            not self.old_report
            or scrabTask['name'] not in self.old_report['tasks']
            or version.parse(self.old_report['tasks'][scrabTask['name']])
            != version.parse(scrabTask['version'])
        )

    def run_tasks(self):
        """
        Executes the scrab tasks on the projects concurrently - each project
        will have its own thread were the scrab tasks are run

        :returns: The report that contains the results of the scrab tasks
        """
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            projects = self.task_yaml['projects']
            reports = {}

            self.__queue_git_projects(projects, futures, executor)
            self.__collect_git_tasks(futures, reports)

        return reports

    def __queue_git_projects(self, projects, futures, executor):
        """
        Queues the projects in the ThreadPoolExecutor

        :param  projects:  The projects
        :param  futures:   The futures that will return the results of the scrab
                           tasks
        :param  executor:  The executor that will execute the projects
        """
        for project in projects:
            futures[executor.submit(
                self.__git_tasks, project)] = project

    def __collect_git_tasks(self, futures, report):
        """
        Collects the results form the scrab tasks on a project basis

        This function is effectively blocking until all results from all futures
        are obtained

        :param  futures:  The futures to collect the results from
        :param  report:   The report to write the sub-reports into
        """
        for future in as_completed(futures):
            project = futures[future]
            result = self.__get_repo_task_result(project, future)

            report[project['url']] = result

    def __get_repo_task_result(self, project, future):
        """
        Gets the git task result.

        :param    project:  The project to get the result from the future from
        :param    future:   The future to get the result from

        :returns: The git task result.
        """
        try:
            return future.result()
        except Exception as e:
            tb = sys.exc_info()[2]
            raise Exception("While working on the git "
                            "ScrabTasks for {} something happened".format(
                                project['url'])).with_traceback(tb)
