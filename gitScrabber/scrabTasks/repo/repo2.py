name = "run2"
version = "1.0.0"


def run2(report, project):
    if('data' not in project):
        handle_scrab_data(report, project)
    else:
        handle_manual_data(report, project)


def handle_scrab_data(report, project):
    pass


def handle_manual_data(report, project):
    if 'authors' in project['data']:
        report['authors'] = project['data']['authors']
    if 'contributors' in project['data']:
        report['contributors'] = project['data']['contributors']
