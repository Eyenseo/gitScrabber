from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
import os
import re

name = "feature_detector"
version = "2.0.0"


class Feature():

    """
    Helper class that stores all information of a specific future as well as
    the queries and compiled regular expressions

    :param    category:  The category of the feature
    :param    name:      The name of the feature
    :param    queries:   The queries to check for
    """

    def __init__(self, category, name, queries):
        self.category = category
        self.name = name

        queries = self.__generate_queries(queries)
        self.simple_queries = queries[0]
        self.regex_queries = queries[1]

    def __generate_queries(self, queries):
        """
        Generates the queries used to determine if a feature is present in a
        file

        As abbreviation are prone to be ambiguous it is important to guarantee
        that they are not part of another word for that Regex is necessary which
        is slower than a normal search. This function decides weather a query is
        unique enough to be used in a normal search

        :param    queries:  The queries to search for, that will probable be
                            converted to regex queries
        """
        simple_queries = []
        regex_queries = []

        for query in queries:
            if len(query) > 3:
                simple_queries.append(query.lower())
            else:
                regex_queries.append(
                    #         not before    search        not after
                    re.compile(r"[^a-z0-9]"+query.lower()+r"[^a-z0-9]"))
        return (simple_queries, regex_queries)


class FeatureDetector():

    """
    Convenience class to detect features in the project files based on search
    queries. The files and queries are handled caseINSENSITIVE and ambiguous
    queries will be wrapped in a regex expression to improve accuracy.

    All files are considered - except files that that are hidden (unix way -
    leading .) as documentation and readme files might also contain hints
    towards features.

    To speed up the process a ThreadPoolManager is utilized as this task is
    mainly IO bound.

    :param  project:         The project to search the features for
    :param  featue_queries:  The feature queries to search for
    """

    def __init__(self, project, featue_queries):
        self.__project = project
        # 5 workers per CPU core
        # we are IO-bound so five times CPU-cores processes is not too much
        self.__executor = ThreadPoolExecutor(max_workers=5)
        self.__futures = {}
        self.__features = self.__make_feature_list(featue_queries)

    def __make_feature_list(self, featue_queries):
        """
        Creates a list of features to check the project files for

        :param    featue_queries:  The feature queries to search for

        :returns: List of features to check the project files for
        """
        features = []
        for category in featue_queries:
            for feature in featue_queries[category]:
                features.append(Feature(
                    category=category,
                    name=feature,
                    queries=featue_queries[category][feature]))
        return features

    def __get_feature_result(self, path, future):
        """
        Gets the feature result.

        :param    path:    The path of the file that was analysed
        :param    future:  The future to get the result from

        :returns: The feature result.
        """
        try:
            return future.result()
        except Exception as e:
            tb = sys.exc_info()[2]
            raise Exception("While collecting the ScrabTask results for '{}'"
                            " something happened".format(path)
                            ).with_traceback(tb)

    def __merge_results(self, first, second):
        """
        Merges the future results together

        :param    first:   Base dictionary that the second dictionary is merged
                           into
        :param    second:  The second dictionary that is merged into the first

        :returns: Merged dictionary that contains the results from the first and
                  second one
        """
        for category in second:
            if category not in first:
                first[category] = {}

            for feature in second[category]:
                if feature not in first[category]:
                    first[category][feature] = 0
                first[category][feature] += second[category][feature]
        return first

    def __read_file(self, filepath):
        """
        Reads a file by trying multiple encoding if necessary

        :param    filepath:  The file path to load the file from

        :returns: String containing the file contents
        """
        try:
            with open(filepath, 'r') as fd:
                return fd.read()
        except Exception as e:
            pass
        try:
            with open(filepath, mode='r', encoding="iso-8859-15") as fd:
                return fd.read()
        except Exception as e:
            pass
        raise Exception("Can't open file - tried encoding 'UTF-8' and "
                        "'iso-8859-15' on file {}".format(filepath))

    def __find_features_in_file(self, filepath):
        """
        Finds features in a file

        :param    filepath:  The file path of the file that the features shall
                             be found in

        :returns: Dictionary containing the numbers of method queries from the
                  features
        """
        file = self.__read_file(filepath).lower()

        feature_counts = {}

        for feature in self.__features:
            if feature.category not in feature_counts:
                feature_counts[feature.category] = {}
            if feature.name not in feature_counts[feature.category]:
                feature_counts[feature.category][feature.name] = 0

            feature_count = 0
            for query in feature.simple_queries:
                feature_count += file.count(query)
            for query in feature.regex_queries:
                feature_count += len(query.findall(file))
            feature_counts[feature.category][feature.name] += feature_count

        return feature_counts

    def __queue_files(self):
        """
        Queues the project files into the ThreadPoolExecutor to be analysed for
        features
        """
        old_path = ""
        for dirpath, dirs, filenames in os.walk(self.__project.location,
                                                topdown=True):
            # ignore hidden / git directories
            if old_path is not dirpath:
                old_path = dirpath
                for d in dirs:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    continue

            for file in filenames:
                if file[0] is '.':
                    # ignore hidden / git files
                    continue
                path = os.path.join(dirpath, file)
                feature = self.__executor.submit(
                    self.__find_features_in_file, path)
                self.__futures[feature] = path

    def __collect_feature_results(self):
        """
        Collects the feature results

        :returns: Merged result directory of the amount of matched queries in
                  the project files
        """
        results = {}
        for future in as_completed(self.__futures):
            project = self.__futures[future]
            result = self.__get_feature_result(project, future)
            self.__merge_results(results, result)
        return results

    def find_features(self):
        """
        Finds feature in the given project's files

        :returns: Directory of the amount of matched queries in
                  the project files
        """
        self.__queue_files()
        return self.__collect_feature_results()


def feature_detector(project_report, project, task_params, global_args):
    """
    Detects features in the project files based on search queries. The files and
    queries are handled caseINSENSITIVE and ambiguous queries will be wrapped in
    a regex expression to improve accuracy

    All files are considered - except files that that are hidden (unix way -
    leading .) as documentation and readme files might also contain hints
    towards features

    To speed up the process a ThreadPoolManager is utilized as this task is
    mainly IO bound.

    :param    project_report:  The project report so far - __DO NOT MODIFY__
    :param    project:         The project
    :param    task_params:     The queries to search for - have to be given in
                               the following data structure:
                               {category: {feature: [query,query]}}
    :param    global_args:     Arguments that will be passed to all tasks. They
                               _might_ contain something that is useful for the
                               task, but the task has to check if it is _there_
                               asthese are user provided. If they are needed to
                               work that check should happen in the argHandler.

    :returns: Directory of the amount of matched queries in the project files
    """
    if (len(task_params) < 1):
        return ("There has to be a map with search queries "
                "{category: {feature: [query,query]}}")
    for category in task_params:
        if (len(task_params[category]) < 1):
            return ("There has to be a map with search queries "
                    "{category: {feature: [query,query]}}")
        for feature in task_params[category]:
            if (len(task_params[category][feature]) < 1):
                return ("There has to be a map with search queries "
                        "{category: {feature: [query,query]}}")

    return FeatureDetector(project, task_params).find_features()
