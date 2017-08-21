from ..scrabTask import ReportTask
from utils import containedStructure

from datetime import datetime, timezone
from math import log2, pow
from dateutil import parser

name = "ImpactCalculator"
version = "1.1.0"


class ImpactData():

    """
    Helper class that stores all information about a single project that is
    needed to calculate the impact

    :param    project_report:    The project report
    :param    language_weights:  The language weights
    """

    def __init__(self, project_report, language_weights):

        self.__project_report = project_report
        self.__language_weights = language_weights

        self.authors = None
        self.contributors = None
        self.language_weight = None
        self.last_change_age = None
        self.project_age = None

        self.__gather_autor_contrib()
        self.__gather_project_dates()
        self.__gather_language_weight()

    def __gather_autor_contrib(self):
        """
        The function gathers the author and contributor amounts that are needed
        to calculate the impact of the project
        """
        report = None

        if 'AuthorContributorCounter' in self.__project_report:
            report = self.__project_report['AuthorContributorCounter']
        else:
            return

        if 'author#' in report and 'contributor#' in report:
            self.authors = report['author#']
            self.contributors = report['contributor#']

    def __gather_project_dates(self):
        """
        The function gathers the first and last change dates that are needed to
        calculate the impact of the project
        """
        report = None
        if 'ProjectDates' in self.__project_report:
            report = self.__project_report['ProjectDates']
        else:
            return

        if 'first_change' in report and 'last_change' in report:
            self.project_age = (
                datetime.now(timezone.utc)
                - parser.parse(report['first_change'])
            ).days
            self.last_change_age = (
                datetime.now(timezone.utc)
                - parser.parse(report['last_change'])
            ).days

    def __gather_language_weight(self):
        """
        The function gathers the language that is needed to calculate the impact
        of the project. The function prefers the git hub information and will
        fall back to our own results generated by a more primitive algorithm
        """
        report = None

        if 'LanguageDetector' in self.__project_report:
            report = self.__project_report['LanguageDetector']
        if 'MetaDataCollector' in self.__project_report:
            if 'main_language' in self.__project_report['MetaDataCollector']:
                report = self.__project_report['MetaDataCollector']

        if not report:
            return

        if ('main_language' in report and report[
                'main_language'] in self.__language_weights):
            self.language_weight = self.__language_weights[
                report['main_language']]

    def usable(self):
        """
        Checks weather all information is available to calculate the impact for
        the given project

        :returns: True if all necessary information is present False otherwise
        """
        return (self.authors is not None
                and self.contributors is not None
                and self.language_weight is not None
                and self.last_change_age is not None
                and self.project_age is not None)


class ImpactCalculator(ReportTask):

    """
    Class to calculate the impact for a single project

    Example:
        impact:
          impact: 45.13200916761271

    :param  parameter:    Parameter given explicitly for this task, for all
                          projects, defined in the task.yaml
    :param  global_args:  Arguments that will be passed to all tasks. They
                          _might_ contain something that is useful for the task,
                          but the task has to check if it is _there_ as these
                          are user provided. If they are needed to work that
                          check should happen in the argHandler.
    """

    def __init__(self, parameter, global_args):
        super(ImpactCalculator, self).__init__(name, version, parameter,
                                               global_args)
        self.__authors_weight = 1
        self.__contributors_weight = .1
        self.__last_change_age_weight = 1
        self.__project_age_weight = 1

        # FIXME think of real weights or generate them
        self.__language_weights = {
            'C++': 1,
            'C': 1,
            'Rust': 1,
            'Ruby': 1,
            'Java': 1,
            'Go': 1,
            'PHP': 1,
            'JavaScript': 1,
            'Objective-C': 1,
            'Swift': 1,
            'C#': 1,
            'Python': 1
        }

        self.__overwrite_weights()

    def __overwrite_weights(self):
        """
        Checks and overwrites the default weights with the ones provided in the
        tasks.yaml file
        """
        if 'authors_weight' in self._parameter:
            self.__authors_weight = self._parameter['authors_weight']
        if 'contributors_weight' in self._parameter:
            self.__contributors_weight = self._parameter['contributors_weight']
        if 'last_change_age_weight' in self._parameter:
            self.__last_change_age_weight = self._parameter[
                'last_change_age_weight']
        if 'project_age_weight' in self._parameter:
            self.__project_age_weight = self._parameter['project_age_weight']
        if 'language_weights' in self._parameter:
            self.__language_weights = {
                **self.__language_weights,
                **self._parameter['language_weights']
            }

    def calculate_impact(self, data):
        """
        Calculates the impact for the given project data

        :returns: The impact of the project, NaN is case not all required
                  information is available in the given project report
        """
        if not data.usable():
            return None

        if data.last_change_age < 90:
            data.last_change_age = 90

        return data.language_weight * (
            (10 - pow(2, log2(10)
                      - self.__contributors_weight * data.contributors))
            + (10 - pow(2, log2(10)
                        - self.__authors_weight * data.authors))
            + self.__last_change_age_weight * (
                10 / pow(2, ((data.last_change_age / 90) - 1)))
            + (10 - pow(2, log2(10)
                        - self.__project_age_weight * data.project_age
                        / 365))
        )

    def scrab(self, report):
        """
        The scrab task calculates for all projects in the report the impact.

        :param    report:       The report to analyse _and_ change

        :returns: Report that contains all scrabbed information
                  Example:
                      impact:
                        impact: 45.13200916761271
        """
        for project in report['projects']:
            impact_data = ImpactData(report['projects'][project],
                                     self.__language_weights)

            impact = self.calculate_impact(impact_data)
            if impact:
                report['projects'][project]['impact'] = {
                    'impact': float("{0:.2f}".format(impact))
                }
            elif not containedStructure(
                    {'projects': {project: {'impact': {'impact': 0}}}},
                    report):
                report['projects'][project]['impact'] = {
                    'impact': None
                }
        return report
