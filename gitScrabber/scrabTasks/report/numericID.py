from ..scrabTask import ReportTask

from utils import containedStructure

name = "NumericID"
version = "1.0.0"


def _get_main_language(project_report):
    """
    Returns the main language from a project report. The reported main language
    from the MetaDataCollector is preferred over  the one reported from
    MetaDataCollector - if either are not present an empty string is returned

    :param    project_report:  The project report

    :returns: The main language if MetaDataCollector or LanguageDetector are
              present in the report or an empty string
    """
    required = {"generalData": {"interfaceLanguage": []}}

    if (containedStructure(required, project_report)
            and len(project_report["generalData"]["interfaceLanguage"]) > 0):
        return project_report["generalData"]["interfaceLanguage"][0]
    return ""  # Return empty -> check will fail


def _is_main_language(project_report, language):
    """
    Determines if main language of the given project matches the given language

    :param    project_report:  The project report
    :param    language:        The language to check against

    :returns: True if main language of the project is the same as the given
              language, False otherwise.
    """
    main_language = _get_main_language(project_report)
    return language == main_language


class NumericID(ReportTask):

    """
    Scrab task that assigns the projects a increasing numeric ID. The
    projects are assigned the ID in order of their main language.

    Example:
        NumericID: 3

    :param  parameter:    Parameter given explicitly for this task, for all
                          projects, defined in the task.yaml
    :param  global_args:  Arguments that will be passed to all tasks. They
                          _might_ contain something that is useful for the task,
                          but the task has to check if it is _there_ as these
                          are user provided. If they are needed to work that
                          check should happen in the argHandler.
    """

    def __init__(self, parameter, global_args):
        super(NumericID, self).__init__(name, version,
                                        parameter, global_args)
        self.__projects = None
        self.__current_id = 1
        self.__languages = [
            'C++',
            'C',
            'Rust',
            'Ruby',
            'Java',
            'Go',
            'PHP',
            'JavaScript',
            'Objective-C',
            'Swift',
            'C#',
            'Python'
        ]

    def __generate_id(self, project_report):
        """
        Generates the numeric ID for the project report and writes it to the
        given report

        :param    project_report:  The project report
        """
        project_report['NumericID'] = self.__current_id
        self.__current_id += 1

    def __generate_ids(self):
        """
        Generates the numeric IDs for the projects in order of their main
        language. Projects without a main language will be given their number
        last.
        """
        for language in self.__languages:
            for project in self.__projects:
                if not _is_main_language(self.__projects[project], language):
                    continue
                self.__generate_id(self.__projects[project])

        for language in self.__languages:
            for project in self.__projects:
                if 'NumericID' in self.__projects[project]:
                    continue
                self.__generate_id(self.__projects[project])

    def scrab(self, report):
        """
        The scrab task assigns the projects a increasing numeric ID. The
        projects are assigned the ID in order of their main language.

        :param    report:       The report to analyse _and_ change

        :returns: Report that contains all scrabbed information
                  Example:
                      NumericID: 3
        """
        self.__projects = report['projects']
        self.__generate_ids()
        return report
