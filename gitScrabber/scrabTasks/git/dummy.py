name = "dummy"
version = "1.0.0"


def dummy(report, project):
    """
    Dummy example - see authorContributerCounter for a better one

    :param    report:   The report
    :param    project:  The project
    """
    if('data' not in project):
        handle_scrab_data(report, project)
    else:
        handle_manual_data(report, project)


def handle_scrab_data(report, project):
    pass


def handle_manual_data(report, project):
    pass
