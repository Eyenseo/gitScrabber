from ..scrabTask import GitTask

import requests

name = "MetaDataCollector"
version = "1.1.0"


class MetaDataCollector(GitTask):
    """
    Class to query the github api to obtain the forks, languages, licence and
    stars of the given repo

    Example:
        MetaDataCollector:
          stars: 5161
          languages:
          - C
          - Perl
          main_language: C
          forks: 2661
          licence:
            name: Academic Free License v3.0
            abb: AFL-3.0

    :param  parameter:    Parameter given explicitly for this task, for all
                          projects, defined in the task.yaml
    :param  global_args:  This class makes use of the github-token to circumvent
                          the tight rate-limiting for the github api

                          https://github.com/settings/tokens
                          https://developer.github.com/v3/#authentication
    """

    def __init__(self,  parameter, global_args):
        super(MetaDataCollector, self).__init__(name, version, parameter,
                                                global_args)
        self.__project = None
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
        replaceStr = None

        if self.__project.url.startswith('git@github.com:'):
            replaceStr = 'git@github.com:'
        elif self.__project.url.startswith('https://github.com/'):
            replaceStr = 'https://github.com/'
        elif self.__project.url.startswith('http://github.com/'):
            replaceStr = 'http://github.com/'
        else:
            raise Exception(
                "Unsupported project - it has to be a github project but "
                "the  url '{}' seems to be not from github.".format(
                    self.__project.url))

        url = self.__project.url.replace(
            replaceStr, 'https://api.github.com/repos/')
        url += urlExtension

        if self._global_args.github_token:
            url += "?access_token="+self._global_args.github_token

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

    def __get_language_data(self):
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
                key=self.__queries['languages'].get
            )
        }

    def __get_forks_count(self):
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

    def __get_stars(self):
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

    def __get_licence(self):
        """
        Queries the github api to obtain the number of stars of the project

        :returns: either 0 or the nr of stars of the project
        """
        if 'licence' not in self.__queries:
            self.__queries['licence'] = self.__access_github_api('/license')

        query = self.__queries['licence']
        name = None
        abb = None

        if ('license' in query and 'name' in query['license']
                and 'Other' != query['license']['name']):
            name = query['license']['name']

            if 'spdx_id' in query['license']:
                abb = query['license']['spdx_id']

        return {
            'name': name,
            "abb": abb
        }

    def scrab(self, project):
        """
        Queries the github api to obtain the forks, languages, licence and
        stars of the given repo

        :param    project:  The project

        :returns: The report of this task as a dictionary
                  Example:
                      MetaDataCollector:
                        stars: 5161
                        languages:
                        - C
                        - Perl
                        main_language: C
                        forks: 2661
                        licence:
                          name: Academic Free License v3.0
                          abb: AFL-3.0
        """
        self.__project = project
        language_data = self.__get_language_data()

        report = {}
        report['stars'] = self.__get_stars()
        report['languages'] = language_data['languages']
        report['main_language'] = language_data['main_language']
        report['forks'] = self.__get_forks_count()
        report['licence'] = self.__get_licence()

        return report
