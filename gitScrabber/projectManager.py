from pyunpack import Archive
from urllib.request import urlopen, Request

import os
import shutil
import tempfile
import utils


class GitProjectManager:
    """
    The GitProjectManager is responsible for executing tasks that scrab at the
    git repos and archives. These tasks are meant to gather data, not
    necessarily interpret it. The interpretation is better left to the report
    scrab task.
    Each GitProjectManager is responsible for a single project and will create
    the portion of the final report that contains the information of this
    project

    :param  project:           The project the scrab tasks run for
    """

    def __init__(self, project):
        self.__project = project

    def __check_repo_folder(self):
        """
        Checks weather the repo folder of the project is indeed a git repo or a
        used folder

        :returns: True if it is a git repo folder False if the folder does not
                  exist

        :exception Exception:  If the folder exists and isn't a git repo
        """
        if os.path.isdir(self.__project.location + '/.git'):
            try:
                utils.run(
                    program='git', args=['status'],
                    cwd=self.__project.location)
            except Exception as e:
                raise Exception(
                    "The git repo '{}' seems to be corrupt "
                    "- please delete it.".format(self.__project.location))
            return True
        else:
            if os.path.isdir(self.__project.location):
                raise Exception("The directory '{}' is used and would be "
                                "overwritten when cloning.".format(
                                    self.__project.location)
                                )
            else:
                return False

    def __init_repo(self):
        """
        Updates the git repo - either cloning it for the first time or pulling
        changes

        :returns: True if anything changed False if nothing changed
        """
        utils.run(
            program='git',
            args=[
                'clone',
                '--recurse-submodules',
                '--shallow-submodules',
                self.__project.url,
                self.__project.location
            ])

    def __update_repo(self):
        """
        Updates the git repo - either cloning it for the first time or pulling
        changes

        :returns: True if anything changed False if nothing changed
        """
        result = utils.run(
            program='git',
            args=['status', '-uno'],
            cwd=self.__project.location
        )
        if 'Your branch is up-to-date' in result:
            return False

        result = utils.run(
            program='git',
            args=['pull', '--recurse-submodules'],
            cwd=self.__project.location
        )
        return True

    def __handle_bad_submodules(self):
        """
        Updates the git repo - either cloning it for the first time or pulling
        changes

        :returns: True if anything changed False if nothing changed
        """
        utils.run(
            program='git',
            args=[
                'submodule',
                'foreach',
                '"git checkout master || (exit 0)"',
            ],
            cwd=self.__project.location
        )

    def update(self):
        """
        This function is responsible to ensure that the source files are
        present. It also decides weather the scrab tasks have to run again based
        in their version and the version mentioned in the old report as well as
        if the source files have changed

        :returns: The sub-report containing all project information of this
                  project
        """

        try:
            if self.__check_repo_folder():
                return self.__update_repo()
            else:
                self.__init_repo()
                return True
        except Exception as e:
            if ("Fetched in submodule path " in str(e)
                    and "Direct fetching of that commit failed." in str(e)):
                self.__handle_bad_submodules()
                return True
            else:
                raise e


class ArchiveProjectManager:
    """
    The ArchiveProjectManager is responsible for executing tasks that scrab at the
    git repos and archives. These tasks are meant to gather data, not
    necessarily interpret it. The interpretation is better left to the report
    scrab task.
    Each ArchiveProjectManager is responsible for a single project and will create
    the portion of the final report that contains the information of this
    project

    :param  project:           The project the scrab tasks run for
    """

    def __init__(self, project):
        self.__project = project

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

    def update(self):
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
