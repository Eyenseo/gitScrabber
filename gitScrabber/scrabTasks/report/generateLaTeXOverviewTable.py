from ..scrabTask import ReportTask

from utils import containedStructure

import regex

name = "GenerateLaTeXOverviewTable"
version = "1.0.0"

__TeX_Specials = {
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\^{}',
    '\\': r'\textbackslash{}',
    '<': r'\textless ',
    '>': r'\textgreater ',
}

__TeX_regex = regex.compile(
    '|'.join(
        regex.escape(key) for key in sorted(
            __TeX_Specials.keys(),
            key=lambda item: - len(item)
        )
    )
)


def _tex_escape(text):
    """
    Escapes special characters in LaTeX

    Taken from https://stackoverflow.com/a/25875504/1935553

    :param    text:  a plain text message

    :returns: the message escaped to appear correctly in LaTeX
    """

    return __TeX_regex.sub(
        lambda match: __TeX_Specials[match.group()],
        text,
        concurrent=True
    )


def _has_interface_language(project_report, language):
    """
    Checks weather a project has a given language as interface language

    :param    project_report:  The project report to get the interface languages
                               from
    :param    language:        The language to check against

    :returns: True if has interface language, False otherwise.
    """
    required = {"generalData": {"interfaceLanguage": []}}

    if not containedStructure(required, project_report):
        raise Exception(
            "There has to be an array with interface languages "
            "{generalData:{interfaceLanguage: [C, C++]}}")
    return language in project_report['generalData']['interfaceLanguage']


def _project_id(project_report):
    """
    Obtains the numeric project id that was generated by the NumericID task from
    the project report

    :param    project_report:  The project report to obtain the numeric project
                               id from

    :returns: The numeric project id as string of length 3 with leading zeros
    """
    required = {"NumericID": 0}
    if not containedStructure(required, project_report):
        return '-'

    return str(project_report['NumericID']).zfill(3)


def _project_name(project_report):
    """
    Obtains the project name from the project report

    :param    project_report:  The project report to obtain the project name
                               from

    :returns: The project name
    """
    required = {"name": ""}
    if not containedStructure(required, project_report):
        raise Exception("There has to be name for the project")

    return _tex_escape(project_report['name'])


def _project_impact(project_report):
    """
    Obtains the project impact that was calculated by the ImpactCalculator task
    from the project report

    :param    project_report:  The project report to obtain the project impact
                               from

    :returns: The project impact
    """
    required = {"impact": 0.0}
    if not containedStructure(required, project_report):
        return '-'

    return project_report['impact']


def _project_size(project_report, language):
    """
    Obtains the project size that was calculated for a specific language by the
    ProjectMetrics task from the project report

    :param    project_report:  The project report to obtain the project size
                               from
    :param    language:        The language the size was calculated for

    :returns: The project size calculated for a specific language
    """
    required = {"ProjectSizeCalculator": {language: ""}}
    if not containedStructure(required, project_report):
        return '-'

    size = project_report['ProjectSizeCalculator'][language]

    if size == "big":
        return r"\myUpDing"
    elif size == "normal":
        return r"\myNormalDing"
    elif size == "small":
        return r"\myDownDing"
    else:
        return '-'


def _project_count_features(project_report, feature_categories):
    """
    Counts the features that have at least one finding found by the
    FeatureDetector scrab task. Inly the feature categories that are specified
    are considered

    :param    project_report:      The project report to count the found
                                   features in
    :param    feature_categories:  The feature categories to consider

    :returns: Count of features found in the given report that belong to one of
              the given categories
    """
    required = {"FeatureDetector": {}}
    if not containedStructure(required, project_report):
        return '-'

    count = 0
    categories = project_report['FeatureDetector']

    for category in categories:
        if category not in feature_categories:
            continue

        for feature in categories[category]:
            if categories[category][feature] > 0:
                count += 1
    return count


def _project_ease_of_use(project_report):
    """
    Obtains the approximated ease of use of the project that was calculated by
    the EaseOfUseEstimation task from the project report

    :param    project_report:  The project report to obtain the projects
                               approximated ease of use from

    :returns: The projects approximated ease of use
    """
    required = {"EaseOfUseEstimation": ""}
    if not containedStructure(required, project_report):
        return '-'

    eou = project_report['EaseOfUseEstimation']

    if eou == "easy":
        return r"\myUpDing"
    elif eou == "normal":
        return r"\myNormalDing"
    elif eou == "difficult":
        return r"\myDownDing"
    else:
        return '-'


def _project_licences(project_report):
    """
    Obtains the project licence from the project report

    :param    project_report:  The project report to obtain the projects
                               licence from

    :returns: The projects licence
    """
    required = {"generalData": {"licences": []}}

    if not containedStructure(required, project_report):
        return '-'

    licences = "\specialcell{"
    first = True
    for licence in project_report['generalData']['licences']:
        if first:
            first = False
        else:
            licences += r'\\'
        licences += _tex_escape(licence)

    return licences + '}'


class GenerateLaTeXOverviewTable(ReportTask):

    """
    Generates a LaTeX table for each interface language to provide an
    overview of the projects. The table is very compact to fit on a A4 page
    and doesn't provide a whole lot of detail.

    Example:
      GenerateLaTeXOverviewTable:
        C++: |-
          \begin{table}
            \centering
            \tabulinesep=4pt
            \setlength{\tabcolsep}{.3em}
            \begin{tabu}{lYrccrrcY}
              \taburowcolors1{white!95!LightGray..white!95!LightGray}
              \rowfont[c]{}
              {}
                & {}
                  & {}
                    & \multicolumn{2}{c}{Size}
                        & \multicolumn{2}{c}{Features}
                            &{}
                              & {}\\
              \rowfont[c]{}
              ID
                & Name
                  & Impact
                    & In
                      & Ov
                        & Pri
                          & Hi
                            & EoU
                              & Licence\\
              \taburowcolors2{white!80!LightGray..white!95!LightGray}
              001
                & ABI
                  & 11.88
                    & \myDownDing
                      & \myDownDing
                        & 0
                          & 0
                            & \myDownDing
                              & \specialcell{MIT\\JSON}\\
            \end{tabu}
            \caption{C++-interface library overview}
            \label{tab:c++-interface-overview}
          \end{table}

    :param  parameter:    Parameter given explicitly for this task, for all
                          projects, defined in the task.yaml
    :param  global_args:  Arguments that will be passed to all tasks. They
                          _might_ contain something that is useful for the task,
                          but the task has to check if it is _there_ as these
                          are user provided. If they are needed to work that
                          check should happen in the argHandler.
    """

    def __init__(self, parameter, global_args):
        super(GenerateLaTeXOverviewTable, self).__init__(name, version,
                                                         parameter,
                                                         global_args)
        self.__projects = None
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
        self.__primitive_categories = self.__get_primitive_categories(
            parameter)
        self.__highlevel_categories = self.__get_highlevel_categories(
            parameter)

    def __get_primitive_categories(self, parameter):
        """
        Obtains the primitive categories from the parameters given to this task

        :param    parameter:  The parameter given to this task

        :returns: The primitive categories from the parameters given to this
                  task
        """
        if not containedStructure({'primitivCategorieses': []}, parameter):
            raise Exception(
                "There has to be an array with the languages "
                "{primitivCategorieses: [block ciphers]}")
        return parameter['primitivCategorieses']

    def __get_highlevel_categories(self, parameter):
        """
        Obtains the highlevel categories from the parameters given to this task

        :param    parameter:  The parameter given to this task

        :returns: The highlevel categories from the parameters given to this
                  task
        """
        if not containedStructure({'highlevelCategories': []}, parameter):
            raise Exception(
                "There has to be an array with the languages "
                "{highlevelCategories: [public key cryptography]}")
        return parameter['highlevelCategories']

    def __header(self):
        """
        Generates the overview table header

        :returns: The overview table header
        """
        TeXheader = r"""\begin{table}
  \centering
  \tabulinesep=4pt
  \setlength{\tabcolsep}{.3em}
  \begin{longtabu}{lYrccrrcY}
    \taburowcolors1{white!95!LightGray..white!95!LightGray}
    \rowfont[c]{}
    {}
      & {}
        & {}
          & \multicolumn{2}{c}{Size}
              & \multicolumn{2}{c}{Features}
                  &{}
                    & {}\\
    \rowfont[c]{}
    ID
      & Name
        & Impact
          & In
            & Ov
              & Pri
                & Hi
                  & EoU
                    & Licence\\
    \taburowcolors2{white!80!LightGray..white!95!LightGray}"""
        return TeXheader

    def __row(self, project_report, language):
        """
        Generates a row from the given project report for the overview table

        :param    project_report:  The project report
        :param    language:        The language

        :returns: A row for the overview table that represents the data in the
                  given project report
        """
        project_id = _project_id(project_report)
        name = _project_name(project_report)
        impact = _project_impact(project_report)
        interface_size = _project_size(project_report, language)
        overall_size = _project_size(project_report, 'total')
        primitive_features = _project_count_features(
            project_report, self.__primitive_categories)
        highlevel_features = _project_count_features(
            project_report, self.__highlevel_categories)
        ease_of_use = _project_ease_of_use(project_report)
        licences = _project_licences(project_report)

        TeXrow = r"""
    {uid}
      & {name}
        & {impact}
          & {interface_size}
            & {overall_size}
              & {primitive_features}
                & {highlevel_features}
                  & {ease_of_use}
                    & {licences}\\""".format(
            uid=project_id,
            name=name,
            impact=impact,
            interface_size=interface_size,
            overall_size=overall_size,
            primitive_features=primitive_features,
            highlevel_features=highlevel_features,
            ease_of_use=ease_of_use,
            licences=licences)
        return TeXrow

    def __tail(self, language):
        """
        Generates the tail of the overview table

        :param    language:  The language

        :returns: The tail of the overview table
        """
        TeXtail = r"""
  \end{longtabu}
  \caption{%s-interface library overview}
  \label{tab:%s-interface-overview}
\end{table}""" % (language, language.lower())
        return TeXtail

    def __interface_table(self, language):
        """
        Generates for the given interface language an overview table

        :param    language:  The interface language to generate the overview
                             table for

        :returns: Table of the given interface language
        """
        table = self.__header()

        for project in self.__projects:
            report = self.__projects[project]
            if _has_interface_language(report, language):
                table += self.__row(report, language)

        table += self.__tail(language)
        return table

    def __overview_tables(self):
        """
        Generates all overview tables

        :returns: Dict of interface languages as key and overview tables as
                  value
        """
        tables = {}
        for lang in self.__languages:
            tables[lang] = self.__interface_table(lang)
        return tables

    def __preamble(self):
        """
        Generates the preamble needed to compile the tables

        :returns: The preamble needed to compile the tables
        """
        TeXpreable = r"""\usepackage{hyperref} % hyper ref "addon"
\usepackage[svgnames,table]{xcolor} % svg colors
\usepackage{pifont} % Symbols and co
\usepackage{longtable} % base for tabu (longtabu)
\usepackage{tabu} % Good table environment - best?
\usepackage{graphicx}
\usepackage{array}


\newcolumntype{Y}{>{\raggedright\let\newline\\\arraybackslash\hspace{0pt}}X}

\newcommand{\specialcell}[2][c]{%
  \setlength{\extrarowheight}{0pt}%
  \def\arraystretch{0}%
  \tabulinesep=0pt%
  \begin{tabular}[#1]{@{}c@{}}#2\end{tabular}%
}

\newcommand{\myscaleding}[2][1]{\scalebox{#1}{\ding{#2}}}

\newcommand{\myUpDing}{\myscaleding[.6]{115}}
\newcommand{\myNormalDing}{\myscaleding[.6]{108}}
\newcommand{\myDownDing}{\myscaleding[.6]{116}}
"""
        return TeXpreable

    def scrab(self, report):
        """
        Generates overview tables for the interface languages of the projects.

        :param    report:  The report to analyse _and_ change

        :returns: Report that contains all scrabbed information and the overview
                  tables

                  Example:
                    GenerateLaTeXOverviewTable:
                      C++: |-
                        \begin{table}
                          \centering
                          \tabulinesep=4pt
                          \setlength{\tabcolsep}{.3em}
                          \begin{tabu}{lYrccrrcY}
                            \taburowcolors1{white!95!LightGray..white!95!LightGray}
                            \rowfont[c]{}
                            {}
                              & {}
                                & {}
                                  & \multicolumn{2}{c}{Size}
                                      & \multicolumn{2}{c}{Features}
                                          &{}
                                            & {}\\
                            \rowfont[c]{}
                            ID
                              & Name
                                & Impact
                                  & In
                                    & Ov
                                      & Pri
                                        & Hi
                                          & EoU
                                            & Licence\\
                            \taburowcolors2{white!80!LightGray..white!95!LightGray}
                            001
                              & ABI
                                & 11.88
                                  & \myDownDing
                                    & \myDownDing
                                      & 0
                                        & 0
                                          & \myDownDing
                                            & \specialcell{MIT\\JSON}\\
                          \end{tabu}
                          \caption{C++-interface library overview}
                          \label{tab:c++-interface-overview}
                        \end{table}
        """
        self.__projects = report['projects']
        report['GenerateLaTeXOverviewTable'] = self.__overview_tables()
        report['GenerateLaTeXOverviewTable']['preamble'] = self.__preamble()
        return report
