import utils
import re

name = "run"
version = "1.0.0"


def run(report, project):
    if('data' not in project):
        handle_scrab_data(report, project)
    else:
        handle_manual_data(report, project)


def get_shrotlog_map(project):
    shortlog = utils.run('git', ['shortlog', '-s', '-n'], project['location'])

    mapped_log = []

    for line in shortlog.split('\n'):
        if line:
            match = re.search('\s*(\d*)\s*(.*)', line)
            mapped_log.append((int(match.group(1)), match.group(2)))
    return mapped_log


def calc_contributor_authors(mapped_shortlog):
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


def handle_scrab_data(report, project):
    mapped_shortlog = get_shrotlog_map(project)
    classified = calc_contributor_authors(mapped_shortlog)

    report['author#'] = len(classified['authors'])
    # report['authors'] = classified['authors']

    report['contributor#'] = len(classified['contributors'])
    # report['contributors'] = classified['contributors']


def handle_manual_data(report, project):
    if 'author#' in project['data']:
        report['author#'] = project['data']['author#']
    # if 'authors' in project['data']:
        # report['authors'] = project['data']['authors']

    if 'contributor#' in project['data']:
        report['contributor#'] = project['data']['contributor#']
    # if 'contributors' in project['data']:
        # report['contributors'] = project['data']['contributors']
