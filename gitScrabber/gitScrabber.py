from scrabTaskManager import ScrabTaskManager
from repoTaskRunner import RepoTaskRunner
from reportTaskRunner import ReportTaskRunner
import ArgHandler

import ruamel.yaml


class GitScrabber:
    """docstring for GitScrabber"""     # TODO

    def __init__(self, args):
        self.args = args
        self.scrabTaskManager = ScrabTaskManager()

        self.yaml = ruamel.yaml.load(
            open(args.tasks, 'r').read(),
            ruamel.yaml.RoundTripLoader)

        if(args.report):
            self.old_report = ruamel.yaml.load(
                open(args.report, 'r').read(),
                ruamel.yaml.RoundTripLoader)
        else:
            self.old_report = None

    def add_scrab_versions(self, report, kind):
        for task in self.yaml['tasks'][kind]:
            scrabTask = self.scrabTaskManager.get_task(task)
            report['tasks'][task] = scrabTask['version']

    def repo_tasks(self, report):
        report['projects'] = RepoTaskRunner(
            self.yaml,
            self.old_report,
            self.scrabTaskManager,
            self.args.gitdir).run_tasks()
        self.add_scrab_versions(report, 'repo')

    def report_tasks(self, report):
        ReportTaskRunner(self.yaml, report, self.scrabTaskManager).run_tasks()
        self.add_scrab_versions(report, 'report')

    def handele_results(self, report):
        if self.args.savereport:
            with open(self.args.savereport, 'w') as outfile:
                ruamel.yaml.dump(
                    report, outfile, Dumper=ruamel.yaml.RoundTripDumper)

        if self.args.printreport:
            print(ruamel.yaml.dump(report, Dumper=ruamel.yaml.RoundTripDumper))

    def scrab(self):
        report = {'tasks': {}}

        self.repo_tasks(report)
        self.report_tasks(report)

        self.handele_results(report)


def main(args=None):
    if args:
        GitScrabber(ArgHandler.parse_args(args)).scrab()
    else:
        GitScrabber(ArgHandler.parse_args()).scrab()

if __name__ == "__main__":
    main(['-t', '../task.yaml'])
