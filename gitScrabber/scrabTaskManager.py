import importlib
import pkgutil
import sys

import scrabTasks.repo
import scrabTasks.report


class ScrabTaskManager:
    """docstring for scrabTaskManager"""    # TODO

    def __init__(self):
        self.__scrabTasks = {}
        self.load_tasks()

    def obtain_name(self, module):
        name = ''
        try:
            name = getattr(module, 'name')
        except Exception as e:
            tb = sys.exc_info()[2]
            raise Exception("You have to specify the name "
                            "of your ScrabTask").with_traceback(tb)

        if(name in self.__scrabTasks):
            raise Exception("The name '{}' is already used for a "
                            "ScrabTask, please use a different one"
                            "for your ScrabTask".format(name))
        return name

    def obtain_version(self, module, name):
        try:
            return getattr(module, 'version')
        except Exception as e:
            tb = sys.exc_info()[2]
            raise Exception("You have to specify the version of your "
                            "ScrabTask: {}".format(name)).with_traceback(tb)

    def obtain_function(self, module, name,):
        try:
            return getattr(module, name)
        except Exception as e:
            tb = sys.exc_info()[2]
            raise Exception("You have to specify a function with the "
                            "very same name as the name attribute of your "
                            "ScrabTask: {}".format(name)).with_traceback(tb)

    def load_tasks(self):
        modules = {**import_submodules(scrabTasks.repo),
                   **import_submodules(scrabTasks.report)}

        for _, module in modules.items():
            name = self.obtain_name(module)
            version = self.obtain_version(module, name)
            function = self.obtain_function(module, name)

            self.__scrabTasks[name] = {
                'name': name, 'function': function, 'version': version}

    def get_task(self, name):
        try:
            return self.__scrabTasks[name]
        except Exception as e:
            tb = sys.exc_info()[2]
            raise Exception(
                "There is no ScrabTask with the name "
                "'{}' registered".format(name)).with_traceback(tb)


def import_submodules(package, recursive=True):
    """ Import all submodules of a module, recursively, including subpackages

    :param package: package (name or actual module)
    :type package: str | module
    :rtype: dict[str, types.ModuleType]

    Taken from http://stackoverflow.com/a/25562415/1935553
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
