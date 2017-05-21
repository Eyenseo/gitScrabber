import utils
import re

name = "author_contributor_counter"
version = "1.0.0"


def author_contributor_counter(report, project):
    """
    Counts the authors and contributors of a repo

    :param  report:   The report
    :param  project:  The project
    """
    if('data' not in project):
        __handle_scrab_data(report, project)
    else:
        __handle_manual_data(report, project)


def __create_shorlog(project):
    """
    Creates a dict that represents the shortlog that git outputs

    :param    project:  The project

    :returns: The shrotlog dict
    """
    shortlog = utils.run('git', ['shortlog', '-s', '-n'], project['location'])
    mapped_log = []

    for line in shortlog.split('\n'):
        if line:
            match = re.search('\s*(\d*)\s*(.*)', line)
            mapped_log.append((int(match.group(1)), match.group(2)))
    return mapped_log


def __calc_contributor_authors(mapped_shortlog):
    """
    Calculates who is considered a contributor  or an author.

    :param    mapped_shortlog:  The mapped shortlog

    :returns: The contributor authors as a dict.
    """
    top_cont, _ = mapped_shortlog[0]
    cutof = top_cont * 0.75     # FIXME This is just for demonstration purposes
    authors = []
    contributors = []

    for count, cont in mapped_shortlog:
        if count >= cutof:
            authors.append((count, cont))
        else:
            contributors.append((count, cont))

    return {'authors': authors, 'contributors': contributors, }


def __handle_scrab_data(report, project):
    """
    Writes the scrabbed data in the report

    :param  report:   The report
    :param  project:  The project
    """
    mapped_shortlog = __create_shorlog(project)
    classified = __calc_contributor_authors(mapped_shortlog)

    report['author#'] = len(classified['authors'])
    # report['authors'] = classified['authors']

    report['contributor#'] = len(classified['contributors'])
    # report['contributors'] = classified['contributors']


def __handle_manual_data(report, project):
    """
    Writes the manually provided data in the report

    :param    report:   The report
    :param    project:  The project
    """

    if 'author#' in project['data']:
        report['author#'] = project['data']['author#']
    # if 'authors' in project['data']:
        # report['authors'] = project['data']['authors']

    if 'contributor#' in project['data']:
        report['contributor#'] = project['data']['contributor#']
    # if 'contributors' in project['data']:
        # report['contributors'] = project['data']['contributors']
