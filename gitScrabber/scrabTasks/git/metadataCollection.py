import requests

name = "metadata_collector"
version = "1.0.0"


def metadata_collector(report, project, global_args):
    """
    finds the stars, languages, forks and downlowads of each given repo

    :param    report:       The report
    :param    project:      The project
    :param    global_args:  Arguments that will be passed to all tasks. They
                            _might_ contain something that is useful for the
                            task, but the task has to check if it is _there_ as
                            these are user provided. If they are needed to work
                            that check should happen in the argHandler.
    """

    report['stars'] = __get_stars(project)
    language_data = __get_language_data(project)
    report['languages'] = language_data['languages']
    report['main_language'] = language_data['main_language']
    # the downloads api is deprecated - doesn't work anymore
    # report['downloads'] = __get(project, '/downloads', 'download_count')
    report['forks'] = __get_forks_count(project)


def __get_language_data(project):
    """
    returns either None or a list of languages

    :param    project:  The project
    """
    data = __get(project, '/languages')
    return {
        'languages': list(data.keys()),
        'main_language': max(data, key=data.get)
    }


def __get_forks_count(project):
    """
    returns either 0 or the nr of forks

    :param    project:  The project
    """
    data = __get(project, '/forks')
    if not data:
        return 0
    else:
        return len(data)


def __get_stars(project):
    """
    returns either 0 or the nr of stars

    :param    project:  The project
    """
    data = __get(project, '')
    if not data:
        return 0
    else:
        return data['stargazers_count']


def __get(project, urlExtension):
    """
    returns a json object or list depending on the url
    requires a personal access token, these can be created here:
        https://github.com/settings/tokens

    :param    project:  The project
    """
    # datei mit client-id & client_secret vorraussetzten
    # https://developer.github.com/v3/#authentication
    projectPath = project['git']
    replaceStr = None
    if 'git@' in projectPath:
        replaceStr = 'git@github.com:'
    elif 'https' in projectPath:
        replaceStr = 'https://github.com/'
    else:
        replaceStr = 'http://github.com/'

    # TODO replace with own access token like so myAccessToken =
    # '123456789012345'
    myAccessToken = 'personalAccessToken'
    url = projectPath.replace(replaceStr, 'https://api.github.com/repos/') + \
        urlExtension+"?access_token="+myAccessToken
    response = requests.get(url)

    __check_for_error(response, url)

    return response.json()


def __check_for_error(response, url):
    if response.status_code < 200 or response.status_code >= 300:
        message = None
        response_json = response.json()

        if 'message' in response_json:
            message = response_json['message']

        if message:
            raise Exception(
                "The error '{}'' occurred with the following message "
                "'{}' while accessing '{}'".format(
                    response.status_code, message, url))
        else:
            raise Exception(
                "The error '{}'' occurred while accessing '{}'".format(
                    response.status_code, url))
