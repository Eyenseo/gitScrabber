import importlib
import pkgutil
import sys

import scrabTasks.git
import scrabTasks.report
import scrabTasks.archive


class ScrabTask():

    """
    Helper class that stores all information about the scrab tasks

    :param    module:  The module that the scrab task is defined in
    :param    kind:    The kind of the scrab task, either 'archive', 'git' or
                       'report'
    """

    def __init__(self, module, kind):

        self.name = self.__obtain_name(module)
        self.version = self.__obtain_version(module, self.name)
        self.function = self.__obtain_function(module, self.name)
        self.kind = kind

    def __obtain_name(self, module):
        """
        Obtains the name of the function that represents the scrab task

        :param    module:  The module the function and function name exists in

        :returns: the name of the function
        """
        name = ''
        try:
            name = getattr(module, 'name')
        except Exception as e:
            tb = sys.exc_info()[2]
            raise Exception("You have to specify the name "
                            "of your ScrabTask").with_traceback(tb)
        return name

    def __obtain_version(self, module, name):
        """
        Obtains the version of the function that represents the scrab task

        :param    module:  The module the function and function version exists
                           in
        :param    name:    The name of the function

        :returns: the version of the function
        """

        try:
            return getattr(module, 'version')
        except Exception as e:
            tb = sys.exc_info()[2]
            raise Exception("You have to specify the version of your "
                            "ScrabTask: '{}'".format(name)).with_traceback(tb)

    def __obtain_function(self, module, name,):
        """
        Obtains the function that represents the scrab task

        :param    module:  The module the function exists in
        :param    name:    The name of the function

        :returns: the version of the function
        """
        try:
            return getattr(module, name)
        except Exception as e:
            tb = sys.exc_info()[2]
            raise Exception("You have to specify a function with the "
                            "very same name as the name attribute of your "
                            "ScrabTask: '{}'".format(name)).with_traceback(tb)


class ScrabTaskManager:
    """
    ScrabTaskManager will load all modules under scrabTasks.archive,
    scrabTasks.git and scrabTasks.report upon instantiation. These have to
    follow a specific format to be called automagically later on.
    """

    def __init__(self):
        self.__scrabTasks = {}
        self.__load_all_tasks()

    def __load_tasks(self, kind, location):
        """
        Loads scrab tasks from a specific location

        :param    kind:  The type of the loaded tasks, either 'archive',
                              'git' or 'report'
        :param    location:   The location to load the tasks from
        """
        modules = {**import_submodules(location)}

        for _, module in modules.items():
            scrab_task = ScrabTask(module=module, kind=kind)

            if(scrab_task.name in self.__scrabTasks):
                raise Exception("The name '{}' is already used for a "
                                "ScrabTask, please use a different one"
                                "for your ScrabTask".format(scrab_task.name))

            self.__scrabTasks[scrab_task.name] = scrab_task

    def __load_all_tasks(self):
        """
        Loads all scrab tasks
        """
        self.__load_tasks('git', scrabTasks.git)
        self.__load_tasks('report', scrabTasks.report)
        self.__load_tasks('archive', scrabTasks.archive)

    def get_task(self, name):
        """
        Gets the task.

        :param    name:  The name of the scrab task to return

        :returns: The scrab task
        """
        try:
            return self.__scrabTasks[name]
        except Exception as e:
            tb = sys.exc_info()[2]
            raise Exception("There is no ScrabTask with the name "
                            "'{}' registered".format(name)).with_traceback(tb)


def import_submodules(package, recursive=True):
    """
    Import all submodules of a module, recursively, including subpackages

    :param    package:    package (name or actual module)
    :type     package:    str | module
    :param    recursive:  if the modules are loaded recursively
    :rtype:   dict[str, types.ModuleType]

    Taken from http://stackoverflow.com/a/25562415/1935553

    :returns: A dict with the modules and module names that were loaded
    """
    if isinstance(package, str):
        package = importlib.import_module(package)
    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + '.' + name
        results[full_name] = importlib.import_module(full_name)
        if recursive and is_pkg:
            results.update(import_submodules(full_name))
    return results
