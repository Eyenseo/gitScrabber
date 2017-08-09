from ..scrabTask import FileTask
import re

name = "FeatureDetector"
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


class FeatureDetector(FileTask):
    """
    Detects features in the project files based on search queries. The files and
    queries are handled caseINSENSITIVE and ambiguous queries will be wrapped in
    a regex expression to improve accuracy.

    All files are considered - except files that that are hidden (unix way -
    leading .) as documentation and readme files might also contain hints
    towards features

    To speed up the process a ThreadPoolManager is utilized as this task is
    mainly IO bound.

    Example:
        FeatureDetector:
          block ciphers:
            AES: 3889
            AES-128: 678
            Blowfish: 18
          hashes:
            MD5: 462
            SHA: 4252

    :param    task_params:     The queries to search for - have to be given in
                               the following data structure:
                               {category: {feature: [query,query]}}
    :param    global_args:     Arguments that will be passed to all tasks. They
                               _might_ contain something that is useful for the
                               task, but the task has to check if it is _there_
                               asthese are user provided. If they are needed to
                               work that check should happen in the argHandler.
    """

    def __init__(self, parameter, global_args):
        super(FeatureDetector, self).__init__(name, version, parameter,
                                              global_args)

        if (len(parameter) < 1):
            raise Exception("There has to be a map with search queries "
                            "{category: {feature: [query,query]}}")
        for category in parameter:
            if (len(parameter[category]) < 1):
                raise Exception("There has to be a map with search queries "
                                "{category: {feature: [query,query]}}")
            for feature in parameter[category]:
                if (len(parameter[category][feature]) < 1):
                    raise Exception("There has to be a map with search queries "
                                    "{category: {feature: [query,query]}}")

        self.__features = self.__make_feature_list(parameter)

    def __make_feature_list(self, featue_queries):
        """
        Creates a list of features to check the project files for

        :param    featue_queries:  The feature queries to search for

        :returns: List of features to check the project files for
        """
        features = []
        for category in featue_queries:
            for feature in featue_queries[category]:
                features.append(
                    Feature(
                        category=category,
                        name=feature,
                        queries=featue_queries[category][feature]))
        return features

    def scrab(self, project, filepath, file):
        """
        Finds features in a file

        :param    project:   The project that the scrab task shall analyse
        :param    filepath:  The filepath to the file that can be analysed
        :param    file:      The file as string that can be analysed

        :returns: Dictionary containing the numbers of queries from the features
        """
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

    def merge(self, first, second):
        """
        Merges the future results together

        :param    first:   The first report (all reports so far)
        :param    second:  The second report (the new report that has to be
                           merged)

        :returns: Merged report that contains the results from the first and
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

    def finish(self, report):
        """
        Last finishing touches may be done here.

        :param    report:  The complete report this task created

        :returns: Report that contains all scrabbed information
                  eg.:
                  FeatureDetector:
                      block ciphers:
                        AES: 3889
                        AES-128: 678
                        Blowfish: 18
                    hashes:
                        MD5: 462
                        SHA: 4252
        """
        return report
