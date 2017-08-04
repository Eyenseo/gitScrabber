from taskExecutionManager import TaskExecutionManager
from scrabTaskManager import ScrabTaskManager
import argHandler

import ruamel.yaml


class GitScrabber:
    """
    A script to scrab information from git repos

    :param  task_file:    yaml file path that holds the task details
    :param  report_file:  yaml file path that holds the results from a previous
                          execution
    :param  output_file:  file path where the results of the execution will be
                          saved
    :param  data_dir:     directory path where the repositories will be cloned
                          to
    :param  print:        If the report should be printed to stdout
    :param  global_args:  Arguments that will be passed to all tasks. They
                          _might_ contain something that is useful for the task,
                          but the task has to check if it is _there_ as these
                          are user provided. If they are needed to work that
                          check should happen in the argHandler.
    """

    def __init__(self,
                 task_file,
                 report_file=None,
                 output_file=None,
                 data_dir=".",
                 print=False,
                 global_args={}):
        self.__scrabTaskManager = ScrabTaskManager()
        self.__output_file = output_file
        self.__data_dir = data_dir
        self.__print = print
        self.__global_args = global_args
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
        if self.__output_file:
            with open(self.__output_file, 'w') as outfile:
                ruamel.yaml.dump(
                    report, outfile, Dumper=ruamel.yaml.RoundTripDumper)

        if self.__print:
            print(ruamel.yaml.dump(report, Dumper=ruamel.yaml.RoundTripDumper))

    def scrab(self):
        """
        Main Function - starts the execution of the scrab tasks

        :returns: the report as python object
        """
        executionManager = TaskExecutionManager(
            self.__data_dir,
            self.__tasks['project_tasks'],
            self.__tasks['report_tasks'],
            self.__tasks['projects'],
            self.__old_report,
            self.__global_args,
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
    args = argHandler.parse_args(args)
    return GitScrabber(
        task_file=args.tasks,
        report_file=args.report,
        output_file=args.output,
        data_dir=args.data,
        print=args.print,
        global_args={'github-token': args.github_token}
    ).scrab()


if __name__ == "__main__":
    main()
