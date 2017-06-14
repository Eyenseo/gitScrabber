import requests

name = "metadata_collector"
version = "1.0.0"


def metadata_collector(report, project):
    """
    finds the stars, languages, forks and downlowads of each given repo

    :param    report:   The report
    :param    project:  The project
    """
    print(requests.get('https://api.github.com/rate_limit').json())
    

    projectPath = project['git']
    url = projectPath.replace('https://github.com/', 'https://api.github.com/repos/')    

    report['stars'] =  __get_stars(project)
    language_data = __get_language_data(project)
    report['languages'] = language_data['languages']
    report['main_language'] = language_data['main_language']
    # the downloads api is deprecated - doesn't work anymore
    #report['downloads'] = __get(project, '/downloads', 'download_count')
    report['forks'] = __get_forks_count(project)

def __get_language_data(project):
    """
    returns either 0 or a list of languages

    :param    project:  The project
    """
    data = __get(project, '/languages')
    if not data:
        return 0
    else:
        maxNumBytes = max(data.values())
        main_language = None
        for key in data:
            if data[key] is maxNumBytes:
                main_language = key

        return {'languages': list(data.keys()), 'main_language': main_language}

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

    :param    project:  The project
    """
    projectPath = project['git']
    url = projectPath.replace('https://github.com/', 'https://api.github.com/repos/')

    url = url+urlExtension
    response = requests.get(url)    

    return response.json()   