from packaging import version
import os
import shutil
import tempfile
from urllib.request import urlopen, Request
from pyunpack import Archive


class ArchiveTaskRunner:
    """
    The ArchiveTaskRunner is responsible for executing tasks that scrab at a
    code that comes from an archive or a git repo

    :param  project:           The project the scrab tasks run for
    :param  tasks:             The tasks that will run for the project
    :param  old_tasks:         The old tasks that were used to generate old_data
    :param  old_data:          The old data that was produced in a previous run
                               with old_tasks
    :param  scrabTaskManager:  The ScrabTaskManager
    """

    def __init__(self, project, tasks, old_tasks, old_data, scrabTaskManager):
        self.__project = project
        self.__tasks = tasks
        self.__old_tasks = old_tasks
        self.__old_data = old_data
        self.__scrabTaskManager = scrabTaskManager

    def __project_cache_exists(self):
        """
        Validates if the cache folder for the project exists

        :returns: True if the cache folder for the project exists other wise
                  false
        """
        cache_dir = self.__project['location']
        return os.path.isdir(cache_dir)

    def __download_archive(self):
        """
        Downloads the project archive to a temporary file

        :returns: The file name of the temporary file
        """
        url = self.__project['archive']
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
        cache_dir = self.__project['location']
        Archive(archive).extractall(cache_dir)

    def __get_server_header(self):
        """
        Gets the server header for the archive with meta information

        :returns: The server header for the archive with meta information
        """
        req = Request(self.__project['archive'], method='HEAD')
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
        cache_dir = self.__project['location']

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
        if 'git' in self.__project:
            return False

        cache_dir = self.__project['location']

        if(not self.__project_cache_exists()):
            return True
        elif not os.path.isfile(os.path.join(cache_dir, 'ArchiveSize.Scrab')):
            cache_dir = self.__project['location']
            shutil.rmtree(cache_dir)
            return True
        else:
            return self.__changed_server_file()

    def __update_archive(self):
        """
        Updates / creates the archive if needed

        :returns: True if the archive was updated, else false
        """
        cache_dir = self.__project['location']

        if self.__check_for_update():
            os.makedirs(cache_dir, exist_ok=True)
            try:
                tmp_archive = self.__download_archive()
                with open(os.path.join(cache_dir, 'ArchiveSize.Scrab'), 'w') as f:
                    f.write(str(os.path.getsize(tmp_archive)))
                self.__extract_archive(tmp_archive)
            finally:
                os.remove(tmp_archive)
            return True
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
            or scrabTask['name'] not in self.__old_tasks
            or version.parse(self.__old_tasks[scrabTask['name']])
            != version.parse(scrabTask['version'])
        )

    def run_tasks(self):
        """
        This function is responsible to ensure that the archive is present -- if
        a git repo is the projects base it is expected to exist. It also decides
        weather the scrab task has to run again based in its version and the
        version mentioned in the old report as well as if a different sized
        archive has been downloaded

        :returns: The sub-report containing all results of the scrab tasks that
                  ran for this project
        """
        report = {}
        updated = self.__update_archive()

        for task_name in self.__tasks:
            scrabTask = self.__scrabTaskManager.get_task(task_name)

            if(updated or self.__changed_task(scrabTask)):
                task_report = {}
                scrabTask['function'](task_report, self.__project)
                report[task_name] = task_report
            elif task_name in self.__old_data:
                report[task_name] = self.__old_data[task_name]
        return report
