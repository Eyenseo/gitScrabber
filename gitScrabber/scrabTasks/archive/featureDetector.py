import os
import yaml

name = "featureDetector"
version = "1.0.0"

featureCount = {}
featureList = {}

def __find_Features(project_dir):
    """
    walk through all files and their lines in the project 
    and check if that line contains one of the predefined keywords
        
    """
    global featureList
    with open('gitScrabber/scrabTasks/archive/features.yaml', 'r') as f:
        featureList = yaml.load(f)    

    for dirpath, dirnames, filenames in os.walk(project_dir):
        for file in filenames:            
            try:
                data = open(os.path.join(dirpath, file), 'r', encoding="iso-8859-15")
                for line in data:                    
                    __check_if_contains_Keyword(line)
            except Exception as e:
                raise e    
            
def __check_if_contains_Keyword(line):
    global featureList
    global featureCount
    for category in featureList:
        for feature in featureList[category]:
            featureDescriptionList = featureList[category][feature]
            #print(featureDescriptionList)                                            
            if featureDescriptionList:
                for word in featureDescriptionList:
                    if word in line:
                        if category not in featureCount:
                            featureCount[category] = {}

                        if feature not in featureCount[category]:
                            featureCount[category][feature] = {}

                        if word not in featureCount[category][feature]:
                            featureCount[category][feature][word] = 0

                        featureCount[category][feature][word] += 1

def __write_to_report(report):
    report['features'] = {}
    for category in featureCount:
        report['features'][category] = {}
        for feature in featureCount[category]:
            report['features'][category][feature] = {}
            for word in featureCount[category][feature]:
                report['features'][category][feature][word] = featureCount[category][feature][word]

def featureDetector(report, project, task_params, global_args):
    """
    Dummy example - see authorContributerCounter for a better one

    :param    report:       The report
    :param    project:      The project
    :param    task_params:  Parameter given explicitly for this task, for all
                            projects, defined in the task.yaml
    :param    global_args:  Arguments that will be passed to all tasks. They
                            _might_ contain something that is useful for the
                            task, but the task has to check if it is _there_ as
                            these are user provided. If they are needed to work
                            that check should happen in the argHandler.
    """
    __find_Features(project['location'])    
    __write_to_report(report)    
