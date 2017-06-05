from scrabTaskManager import ScrabTaskManager
from repoTaskRunner import RepoTaskRunner
from reportTaskRunner import ReportTaskRunner
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

    def __add_scrab_versions(self, report, kind):
        """
        Adds the ScrabTask versions to the report

        :param  report:  the report to write into
        :param  kind:    the kind of scrabber to add - either repo or report
        """
        for task in self.__tasks['tasks'][kind]:
            scrabTask = self.__scrabTaskManager.get_task(task)
            report['tasks'][task] = scrabTask['version']

    def __repo_tasks(self, report):
        """
        Executes the RepoTaskRunner

        :param  report:  report to write into
        """
        report['projects'] = RepoTaskRunner(
            self.__tasks,
            self.__old_report,
            self.__scrabTaskManager,
            self.__git_dir).run_tasks()
        self.__add_scrab_versions(report, 'repo')

    def __report_tasks(self, report):
        """
        Executes the ReportTaskRunner

        :param  report:  report to write into
        """
        ReportTaskRunner(self.__tasks, report,
                         self.__scrabTaskManager).run_tasks()
        self.__add_scrab_versions(report, 'report')

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

        :returns: the report as python objects
        """
        report = {'tasks': {}}

        self.__repo_tasks(report)
        self.__report_tasks(report)

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
