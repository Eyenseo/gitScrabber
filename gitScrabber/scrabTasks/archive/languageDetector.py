import os

name = "languageDetector"
version = "1.0.0"


def languageDetector(report, project, global_args):
    dir_ = project['location']
    print(project)

    number_of_files = 0
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

    for dirpath, dirnames, filenames in os.walk(dir_):
        for file in filenames:
            filename, file_extension = os.path.splitext(file)
            for language in language_extensions:
                if file_extension in language_extensions[language]:
                    files_per_language[language] += 1
    print(files_per_language)
    max_files = 0
    max_lang = 'Not detected'
    for language in files_per_language:
        if max_files < files_per_language[language]:
           max_lang = language
           max_files = files_per_language[language]
    print(max_files)
    print(max_lang)
    if 'C' is max_lang and files_per_language['C++'] > 5:
        max_lang = 'C++'
    report['language'] = max_lang

    # return {}
