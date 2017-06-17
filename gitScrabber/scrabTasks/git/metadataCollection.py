import requests

name = "metadata_collector"
version = "1.0.0"


class MetaDataCollector():
    """
    Convenience class to querie the github api to obtain the stars, languages
    and forks of the given repo

    :param    project:      The project
    :param    global_args:  This class makes use of the github-token to
                            circumvent the tight rate-limiting for the github
                            api

                            https://github.com/settings/tokens
                            https://developer.github.com/v3/#authentication
    """

    def __init__(self, project, global_args):
        self.__project = project
        self.__global_args = global_args
        self.__queries = {}

    def __check_for_error(self, response, url):
        """
        Checks for errors in the response of the github api

        :param    response:  The response of the api query
        :param    url:       The query url as error information
        """
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

    def __generate_api_url(self, urlExtension):
        """
        Generates the github api query url.

        If a acces token was provided via 'github-token' it will be used here

        :param    urlExtension:  The url extension for the specific api point

        :returns: The url to query the github api
        """
        project_url = self.__project['git']
        replaceStr = None

        if project_url.startswith('git@github.com:'):
            replaceStr = 'git@github.com:'
        elif project_url.startswith('https://github.com/'):
            replaceStr = 'https://github.com/'
        elif project_url.startswith('http://github.com/'):
            replaceStr = 'http://github.com/'
        else:
            raise Exception(
                "Unsupported project - it has to be a github project but "
                "the  url '{}' seems to be not from github.".format(
                    project_url))

        url = project_url.replace(replaceStr, 'https://api.github.com/repos/')
        url += urlExtension

        if self.__global_args['github-token']:
            url += "?access_token="+self.__global_args['github-token']

        return url

    def __access_github_api(self, urlExtension):
        """
        Accesses the github api for the provided url extension e.g.:
            urlExtension='/languages'
            =>
            https://api.github.com/repos//languages

        :param    urlExtension:  The url extension

        :returns: a json object or list depending on the url
        """
        url = self.__generate_api_url(urlExtension)

        response = requests.get(url)
        self.__check_for_error(response, url)

        return response.json()

    def get_language_data(self):
        """
        Queries the github api to obtain the languages used in the project

        :returns: the a list of languages used in the project
        """
        if 'languages' not in self.__queries:
            self.__queries[
                'languages'] = self.__access_github_api('/languages')

        return {
            'languages': list(self.__queries['languages'].keys()),
            'main_language': max(
                self.__queries['languages'],
                key=self.__queries['languages'].get)
        }

    def get_forks_count(self):
        """
        Queries the github api to obtain the number of forks of the project

        :returns: either 0 or the nr of forks of the project
        """
        if '' not in self.__queries:
            self.__queries[''] = self.__access_github_api('')

        if 'forks' not in self.__queries['']:
            return 0
        else:
            return self.__queries['']['forks']

    def get_stars(self):
        """
        Queries the github api to obtain the number of stars of the project

        :returns: either 0 or the nr of stars of the project
        """
        if '' not in self.__queries:
            self.__queries[''] = self.__access_github_api('')

        if 'stargazers_count' not in self.__queries['']:
            return 0
        else:
            return self.__queries['']['stargazers_count']


def metadata_collector(report, project, global_args):
    """
    Queries the github api to obtain the stars, languages and forks of the given
    repo

    :param    report:       The report
    :param    project:      The project
    :param    global_args:  This task scrubber makes use of the github-token to
                            circumvent the tight rate-limiting for the github
                            api

                            https://github.com/settings/tokens
                            https://developer.github.com/v3/#authentication
    """

    meta = MetaDataCollector(project, global_args)

    language_data = meta.get_language_data()

    report['stars'] = meta.get_stars()
    report['languages'] = language_data['languages']
    report['main_language'] = language_data['main_language']
    report['forks'] = meta.get_forks_count()
