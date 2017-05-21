from concurrent.futures import ThreadPoolExecutor, as_completed
from packaging import version
import utils
import sys
import os


class RepoTaskRunner:
    """docstring for RepoTaskRunner"""  # TODO

    def __init__(self, task_yaml, old_report, scrabTaskManager, git_dir):
        super(RepoTaskRunner, self).__init__()
        self.max_workers = 10
        self.task_yaml = task_yaml
        self.old_report = old_report
        self.scrabTaskManager = scrabTaskManager
        self.git_dir = git_dir
        if(not git_dir.endswith('/')):
            self.git_dir += '/'

    def repo_tasks(self, project):
        report = {}
        updated = True

        if('data' not in project):
            updated = self.update_repo(self.git_dir, project['url'])
            project['location'] = self.get_repo_location(
                self.git_dir, project['url'])

        for task_name in self.task_yaml['tasks']['repo']:
            scrabTask = self.scrabTaskManager.get_task(task_name)

            if(updated or self.changed_task(scrabTask)):
                task_report = {}
                scrabTask['function'](task_report, project)
                report[scrabTask['name']] = task_report
            else:
                report[scrabTask['name']] = self.old_report[
                    'projects'][project['url']][scrabTask['name']]

        return report

    def get_repo_location(self, cwd, url):
        return cwd + '/' + url.rsplit('/', 1)[-1]

    def check_repo_folder(self, repo):
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

    def update_repo(self, cwd, url):
        repo_location = self.get_repo_location(cwd, url)

        if(self.check_repo_folder(repo_location)):
            result = utils.run(program='git', args=['pull'], cwd=repo_location)
            if 'Already up-to-date' in result:
                return False
        else:
            utils.run(program='git', args=['clone', url], cwd=cwd)
        return True

    def changed_task(self, scrabTask):
        return\
            not self.old_report\
            or scrabTask['name'] not in self.old_report['tasks']\
            or version.parse(self.old_report['tasks'][scrabTask['name']])\
            != version.parse(scrabTask['version'])

    def run_tasks(self):
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            projects = self.task_yaml['projects']
            reports = {}

            self.queue_repo_tasks(projects, futures, executor)
            self.collect_repo_tasks(futures, reports)

        return reports

    def queue_repo_tasks(self, projects, futures, executor):
        for project in projects:
            futures[executor.submit(
                self.repo_tasks, project)] = project

    def collect_repo_tasks(self, futures, reports):
        for future in as_completed(futures):
            project = futures[future]
            result = self.get_repo_task_result(project, future)

            reports[project['url']] = result

    def get_repo_task_result(self, project, future):
        try:
            return future.result()
        except Exception as e:
            tb = sys.exc_info()[2]
            raise Exception("While working on the repo "
                            "ScrabTasks for {} something happened".format(
                                project['url'])).with_traceback(tb)
