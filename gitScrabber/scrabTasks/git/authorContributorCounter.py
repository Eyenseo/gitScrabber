import utils
import re

name = "author_contributor_counter"
version = "1.0.0"


def __create_shortlog(project):
    """
    Creates a dict that represents the shortlog that git outputs

    :param    project:  The project

    :returns: The shortlog dict
    """
    shortlog = utils.run('git', ['shortlog', '-s', '-n', '--no-merges'], project['location'])
    mapped_log = []

    for line in shortlog.split('\n'):
        if line:
            match = re.search('\s*(\d*)\s*(.*)', line)
            #                  (number of commits, author name)
            mapped_log.append((int(match.group(1)), match.group(2)))
    return mapped_log


def __calc_cutof(mapped_shortlog):
    """
    Calculates where the hard cut of for authors should be.

    This is needed for linear decreasing commit graphs per author, where the
    difference between the amount of commits between the authors is too small to
    result in a rejection

    :param    mapped_shortlog:  The mapped shortlog

    :returns: Hard cut of value for the author contributor classification.
    """
    top_cont, _ = mapped_shortlog[0]
    mean_cut = top_cont * 0.05

    summ = 0
    numm = 0
    for count, _ in mapped_shortlog:
        if count >= mean_cut:
            summ += count
            numm += 1
        else:
            break
    return summ / numm


def __calc_contributor_authors(mapped_shortlog):
    """
    Calculates who is considered a contributor or an author.

    The calculation is done by the difference in commits between authors and a
    hard cut of.

    :param    mapped_shortlog:  The mapped shortlog

    :returns: The contributor authors as a dict.
    """
    authors = []
    contributors = []

    cutof = __calc_cutof(mapped_shortlog)
    prev_count, _ = mapped_shortlog[0]

    for count, cont in mapped_shortlog:
        if count >= cutof and count >= prev_count*0.4:
            prev_count = count
            authors.append((count, cont))
        else:
            contributors.append((count, cont))

    return {'authors': authors, 'contributors': contributors, }


def author_contributor_counter(report, project):
    """
    Counts the authors and contributors of a repo

    :param  report:   The report
    :param  project:  The project
    """
    mapped_shortlog = __create_shortlog(project)
    classified = __calc_contributor_authors(mapped_shortlog)

    report['author#'] = len(classified['authors'])
    # report['authors'] = classified['authors']

    report['contributor#'] = len(classified['contributors'])
    # report['contributors'] = classified['contributors']
