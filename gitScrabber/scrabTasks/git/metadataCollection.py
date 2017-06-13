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

    report['stars'] = __get(project, '', 'stargazers_count') 
    report['languages'] = __get_languages(project)
    # the downloads api is deprecated - doesn't work anymore
    report['downloads'] = __get(project, '/downloads', 'download_count')
    report['forks'] = __get_forks_count(project)

def __get_languages(project):
	"""
    returns either 0 or a list of languages

    :param    project:  The project
	"""

    data = __get(project, '/languages', None)    
    if isinstance( data, int ):
        return data
    else:
    	return list(data.keys())

def __get_forks_count(project):
	"""
    returns either 0 or a the nr of forks

    :param    project:  The project
	"""
	data = __get(project, '/forks', None)
	if data != 0:	    
	    return len(data)
	return data


def __get(project, urlExtension, fieldName):
    """
    returns either 0 if data object is empty, the entire data object, or the value to a given key 

    :param    project:  The project
	"""
    projectPath = project['git']
    url = projectPath.replace('https://github.com/', 'https://api.github.com/repos/')

    url = url+urlExtension
    response = requests.get(url)
    data = response.json()    

    if not data:
    	return 0
    elif fieldName is None:
        return data
    else:    	
        return data[fieldName] 