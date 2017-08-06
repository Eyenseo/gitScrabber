from packaging import version
import utils
import os
import shutil
import tempfile
from urllib.request import urlopen, Request
from pyunpack import Archive


class ProjectTaskRunner:
    """
    The ProjectTaskRunner is responsible for executing tasks that scrab at the
    git repos and archives. These tasks are meant to gather data, not
    necessarily interpret it. The interpretation is better left to the report
    scrab task.
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

    def __init__(self, project, tasks, old_tasks, old_data,
                 global_args, scrabTaskManager):
        self.__project = project
        self.__tasks = tasks
        self.__old_tasks = old_tasks
        self.__old_data = old_data
        self.__global_args = global_args
        self.__scrabTaskManager = scrabTaskManager

        self.__project_to_task_mapping = {
            'archive': ['archive'],
            'git': ['git', 'archive']
        }

    def __check_repo_folder(self):
        """
        Checks weather the repo folder of the project is indeed a git repo or a
        used folder

        :returns: True if it is a git repo folder False if the folder does not
                  exist

        :exception Exception:  If the folder exists and isn't a git repo
        """
        cache_dir = self.__project.location

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
        cache_dir = self.__project.location
        url = self.__project.url

        if(self.__check_repo_folder()):
            result = utils.run(program='git', args=['pull', ], cwd=cache_dir)
            if 'Already up-to-date' in result:
                return False
        else:
            utils.run(
                program='git',
                args=[
                    'clone',
                    '--recurse-submodules',
                    '--shallow-submodules',
                    url,
                    cache_dir
                ])
        return True

    def __project_cache_exists(self):
        """
        Validates if the cache folder for the project exists

        :returns: True if the cache folder for the project exists other wise
                  false
        """
        cache_dir = self.__project.location
        return os.path.isdir(cache_dir)

    def __download_archive(self):
        """
        Downloads the project archive to a temporary file

        :returns: The file name of the temporary file
        """
        url = self.__project.url
        tmp_archive, tmp_archive_name = tempfile.mkstemp(
            suffix=url.rsplit('/', 1)[-1])

        with urlopen(url) as response, open(tmp_archive, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        return tmp_archive_name

    def __extract_archive(self, archive):
        """
        Extracts the given archive to the projects cache folder

        :param    archive:  The archive to extract
        """
        cache_dir = self.__project.location
        Archive(archive).extractall(cache_dir)

    def __get_server_header(self):
        """
        Gets the server header for the archive with meta information

        :returns: The server header for the archive with meta information
        """
        req = Request(self.__project.url, method='HEAD')
        with urlopen(req) as response:
            return {k.lower(): v for k, v in dict(response.info()).items()}

    def __changed_server_file(self):
        """
        Checks if the file on the server has a different size that the local one
        had

        This is by no means a good way to check if there were changes, good
        enough for the 'moment'.

        :returns: True if the remote file size is not equal to the local one
        """
        header = self.__get_server_header()

        if 'content-length' not in header:
            print("4")
            return True

        server_size = header['content-length']
        cache_dir = self.__project.location

        with open(os.path.join(cache_dir, 'ArchiveSize.Scrab'), 'r') as f:
            if int(f.read()) != int(server_size):
                return True
        return False

    def __check_for_update(self):
        """
        Checks if an update of the source code is necessary

        :returns: True it the archive should be downloaded and replace the
                  current code
        """
        cache_dir = self.__project.location

        if(not self.__project_cache_exists()):
            return True
        elif not os.path.isfile(os.path.join(cache_dir, 'ArchiveSize.Scrab')):
            cache_dir = self.__project.location
            shutil.rmtree(cache_dir)
            return True
        else:
            return self.__changed_server_file()

    def __update_archive(self):
        """
        Updates / creates the archive if needed

        :returns: True if the archive was updated, else false
        """
        cache_dir = self.__project.location

        if self.__check_for_update():
            os.makedirs(cache_dir, exist_ok=True)
            try:
                tmp_archive = self.__download_archive()
                size_file = open(os.path.join(
                    cache_dir, 'ArchiveSize.Scrab'), 'w')
                with size_file as f:
                    f.write(str(os.path.getsize(tmp_archive)))
                self.__extract_archive(tmp_archive)
            finally:
                os.remove(tmp_archive)
            return True
        return False

    def __update_project(self):
        """
        Updates the project - either cloning / pulling or re-/downloading it

        :returns: True if anything changed False if nothing changed
        """
        if self.__project.kind == 'git':
            return self.__update_repo()
        elif self.__project.kind == 'archive':
            return self.__update_archive()
        else:
            # TODO handle manually downloaded archives
            pass

        return False

    def __changed_task(self, scrabTask):
        """
        Checks weather the scrab task has to be rerun based on an old report
        and the scab task versions

        :param    scrabTask:  The scrab task to check against

        :returns: True if the scrab task has to rerun False otherwise
        """
        return(
            not self.__old_tasks
            or scrabTask.name not in self.__old_tasks
            or version.parse(self.__old_tasks[scrabTask.name])
            != version.parse(scrabTask.version)
        )

    def run_tasks(self):
        """
        This function is responsible to ensure that the source files are
        present. It also decides weather the scrab tasks have to run again based
        in their version and the version mentioned in the old report as well as
        if the source files have changed

        :returns: The sub-report containing all project information of this
                  project
        """
        report = {}
        updated = self.__update_project()
        tasks_to_do = self.__project_to_task_mapping[self.__project.kind]

        for task in self.__tasks:
            scrabTask = self.__scrabTaskManager.get_task(task.name)

            if (scrabTask.kind in tasks_to_do
                    and (updated or self.__changed_task(scrabTask))):
                task_report = scrabTask.function(report,
                                                 self.__project,
                                                 task.parameter,
                                                 self.__global_args)
                report[task.name] = task_report
            elif self.__old_data and task.name in self.__old_data:
                report[task.name] = self.__old_data[task.name]

        return report
