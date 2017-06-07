from taskExecutionManager import TaskExecutionManager
from scrabTaskManager import ScrabTaskManager
import ArgHandler

import ruamel.yaml


class GitScrabber:
    """
    A script to scrab information from git repos

    :param  task_file:        yaml file path that holds the task details
    :param  report_file:      yaml file path that holds the results from a
                              previous execution
    :param  save_file:        file path where the results of the execution will
                              be saved
    :param  git_dir:          directory path where the repositories will be
                              cloned to
    :param  printing:         If the report should be printed to stdout
    :param  force_overwrite:  If the file that save_file points to should be
                              overwritten
    """

    def __init__(self,
                 task_file,
                 report_file=None,
                 save_file=None,
                 git_dir=".",
                 printing=False,
                 force_overwrite=False):
        self.__scrabTaskManager = ScrabTaskManager()
        self.__save_file = save_file
        self.__printing = printing
        self.__git_dir = git_dir
        self.__tasks = ruamel.yaml.load(
            open(task_file, 'r').read(),
            ruamel.yaml.RoundTripLoader)

        if(report_file):
            self.__old_report = ruamel.yaml.load(
                open(report_file, 'r').read(),
                ruamel.yaml.RoundTripLoader)
        else:
            self.__old_report = None

    def __handele_results(self, report):
        """
        Writes the results of the scrab tasks to file and or to stdout

        :param  report:  report to write
        """
        if self.__save_file:
            with open(self.__save_file, 'w') as outfile:
                ruamel.yaml.dump(
                    report, outfile, Dumper=ruamel.yaml.RoundTripDumper)

        if self.__printing:
            print(ruamel.yaml.dump(report, Dumper=ruamel.yaml.RoundTripDumper))

    def scrab(self):
        """
        Main Function - starts the execution of the scrab tasks

        :returns: the report as python object
        """
        executionManager = TaskExecutionManager(
            self.__git_dir,
            self.__tasks['tasks'],
            self.__tasks['projects'],
            self.__old_report,
            self.__scrabTaskManager)
        report = executionManager.create_report()

        self.__handele_results(report)

        return report


def main(args=None):
    """
    Module main function

    :param    args:  Commandline arguments that will be parsed

    :returns: The results of the scrab method
    """
    args = ArgHandler.parse_args(args)
    return GitScrabber(
        task_file=args.tasks,
        report_file=args.report,
        save_file=args.savereport,
        git_dir=args.gitdir,
        printing=args.printreport,
        force_overwrite=args.force
    ).scrab()


if __name__ == "__main__":
    main(['-t', '../task.yaml', '-p', '-g', '/tmp'])
