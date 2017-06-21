import os

name = "languageDetector"
version = "1.0.0"


def languageDetector(report, project, global_args):
    """
    Tries to detect the programming language of a library 
    based on the file extension

    :param  report:       The report
    :param  project:      The project
    :param  global_args:  This task scrubber makes use of the github-token to
                          circumvent the tight rate-limiting for the github
                          api

                          https://github.com/settings/tokens
                          https://developer.github.com/v3/#authentication
    """
    dir_ = project['location']

    # dictionary containing the common file extensions 
    # for each of the languages
    language_extensions = {
        'C++':  ['.cpp', '.c++', '.cc', '.C', '.cxx'],
        'C':    ['.c'],
        'Rust': ['.rs', '.rlib'],
        'Ruby': ['.rb'],
        'Java': ['.java', '.class', '.jar'],
        'Go':   ['.go'],
        'PHP':  ['.php', '.phtml', '.php3', '.php4', '.php5', '.php7', '.phps'],
        'JavaScript':   ['.js'],
        'Objective-C':  ['.m', '.mm', '.C'],
        'Swift':    ['.swift'],
        'C#':   ['.cs'],
        'Python':   ['.py', '.pyc', '.pyd', '.pyo', '.pyw', '.pyz']
    }

    # count the files that have an extension of one of the languages
    files_per_language = {
        'C++':  0,
        'C':    0,
        'Rust': 0,
        'Ruby': 0,
        'Java': 0,
        'Go':   0,
        'PHP':  0,
        'JavaScript':   0,
        'Objective-C':  0,
        'Swift':    0,
        'C#':   0,
        'Python':   0,
    }

    # walk through all files in the project and count extensions
    for dirpath, dirnames, filenames in os.walk(dir_):
        for file in filenames:
            filename, file_extension = os.path.splitext(file)
            for language in language_extensions:
                if file_extension in language_extensions[language]:
                    files_per_language[language] += 1
    
    # find the language with the maximal amount of files
    max_files = 0
    max_lang = 'Not detected'
    for language in files_per_language:
        if max_files < files_per_language[language]:
           max_lang = language
           max_files = files_per_language[language]
   
    # as C and C++ share the same extensions .c we assume to have a C++
    # project if there are at least 5 files with a C++ extension
    if 'C' is max_lang and files_per_language['C++'] > 5:
        max_lang = 'C++'

    # write the result to the report
    report['language'] = max_lang
