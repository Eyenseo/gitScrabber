from ..scrabTask import FileTask
import utils

from pkg_resources import resource_filename

import os
import json

import regex
import math
from collections import Counter


name = "LicenceDetector"
version = "1.0.0"


class Licence():

    def __init__(self, name, length, vector):
        self.name = name
        self.length = length
        self.vector = vector


def mean(numbers):
    return float(sum(numbers)) / max(len(numbers), 1)


class LicenceDetector(FileTask):

    def __init__(self, parameter, global_args):
        super(LicenceDetector, self).__init__(name, version, parameter,
                                              global_args)

        self.__word_regex = regex.compile(r'\w+')
        self.__licences = self.__generate_licences()

        self.__med_length = mean([node.length for node in self.__licences])
        self.__max_length = max(node.length for node in self.__licences)

        self.__files = [
            '.h', '.hpp', '.hxx', '.rs', '.java', '.go', '.js', '.m', '.mm',
            '.C', '.swift', '.cs', '.php', '.phtml', '.php3', '.php4', '.php5',
            '.php7', '.phps', '.py', '.rb']

    def __read_licences(self, filepath):
        licences = []
        with open(filepath, 'r') as fh:
            licence = json.load(fh)
            name = licence['name']

            if 'licenseText' in licence:
                licences.append(
                    Licence(name,
                            len(licence['licenseText']),
                            self.__text_to_vector(licence['licenseText'])))
            elif 'standardLicenseTemplate' in licence:
                licences.append(
                    Licence(name,
                            len(licence['standardLicenseTemplate']),
                            self.__text_to_vector(
                                licence['standardLicenseTemplate'])))

            if 'standardLicenseHeader' in licence:
                licences.append(
                    Licence(name+' Header',
                            len(licence['standardLicenseHeader']),
                            self.__text_to_vector(
                                licence['standardLicenseHeader'])))

        return licences

    def __generate_licences(self):
        json_licence_dir = os.path.abspath(
            resource_filename('gitScrabber', 'license-list-data/json/details'))
        licences = []

        for file in os.listdir(json_licence_dir):
            if file.endswith(".json"):
                filepath = os.path.join(json_licence_dir, file)
                licences.extend(self.__read_licences(filepath))
        return licences

    def __get_cosine(self, vec1, vec2):
        # https://stackoverflow.com/a/15174569/1935553
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])

        sum1 = sum([vec1[x]**2 for x in vec1.keys()])
        sum2 = sum([vec2[x]**2 for x in vec2.keys()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)

        if not denominator:
            return 0.0
        else:
            return float(numerator) / denominator

    def __text_to_vector(self, text):
        words = self.__word_regex.findall(text.lower(), concurrent=True)
        return Counter(words)

    def scrab(self, project, filepath, file):
        report = {'licence': {}}

        filename, file_extension = os.path.splitext(filepath)
        filename = os.path.basename(filename)

        if (file_extension in self.__files
                or filename.lower() == 'copying'
                or filename.lower() == 'licence'
                or filename.lower() == 'license'
                or filename.lower() == 'acknowledgements'
                or filename.lower() == 'acknowledgement'
                or filename.lower() == 'readme'):

            file_vec_med = self.__text_to_vector(
                file[:int(self.__med_length * 1.3)])
            file_vec_max = self.__text_to_vector(
                file[:int(self.__max_length * 1.3)])

            for licence in self.__licences:
                cosine = 0

                if licence.length < self.__med_length:
                    cosine = self.__get_cosine(file_vec_med, licence.vector)
                else:
                    cosine = self.__get_cosine(file_vec_max, licence.vector)

                if cosine > .98:
                    if filepath not in report['licence']:
                        report['licence'][filepath] = []

                    report['licence'][filepath].append({
                        'licence': licence.name,
                        'confidence': float("{0:.2f}".format(cosine*100))})

            if filepath in report['licence']:
                report['licence'][filepath] = sorted(
                    report['licence'][filepath],
                    key=lambda k: k['confidence'], reverse=True)

        return report

    def merge(self, first, second):
        return utils.deep_merge(first, second)

    def finish(self, report):
        return report
