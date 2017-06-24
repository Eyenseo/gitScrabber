import os

name = "languageDetector"
version = "1.0.0"


cpp_extensions = ['.cpp', '.c++', '.cc', '.cxx', '.c', '.h', '.hpp', '.hxx']
c_extensions = ['.c', '.h']
rust_extensions = ['.rs']
ruby_extensions = ['.rb']
java_extensions = ['.java']
go_extensions = ['.go']
php_extensions = ['.php', '.phtml', '.php3', '.php4', '.php5', '.php7',
                  '.phps']
js_extensions = ['.js']
objective_c_extensions = ['.h', '.m', '.mm', '.C']
swift_extensions = ['.swift']
c_sharp_extensions = ['.cs']
python_extensions = ['.py']


def get_language_extensions():
    return {
        'C++':  cpp_extensions,
        'C':    c_extensions,
        'Rust': rust_extensions,
        'Ruby': ruby_extensions,
        'Java': java_extensions,
        'Go':   go_extensions,
        'PHP':  php_extensions,
        'JavaScript':   js_extensions,
        'Objective-C':  objective_c_extensions,
        'Swift':    swift_extensions,
        'C#':   c_sharp_extensions,
        'Python':   python_extensions
    }


def get_files_per_language():
    return {
        'C++':  {extension: 0 for extension in cpp_extensions},
        'C':    {extension: 0 for extension in c_extensions},
        'Rust': {extension: 0 for extension in rust_extensions},
        'Ruby': {extension: 0 for extension in ruby_extensions},
        'Java': {extension: 0 for extension in java_extensions},
        'Go':   {extension: 0 for extension in go_extensions},
        'PHP':  {extension: 0 for extension in php_extensions},
        'JavaScript':   {extension: 0 for extension in js_extensions},
        'Objective-C':  {extension: 0 for extension in objective_c_extensions},
        'Swift':    {extension: 0 for extension in swift_extensions},
        'C#':   {extension: 0 for extension in c_sharp_extensions},
        'Python':   {extension: 0 for extension in python_extensions},
    }


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
    language_extensions = get_language_extensions()

    # count the files that have an extension of one of the languages
    files_per_language = get_files_per_language()

    # walk through all files in the project and count extensions
    for dirpath, dirnames, filenames in os.walk(dir_):
        for file in filenames:
            filename, file_extension = os.path.splitext(file)
            for language in language_extensions:
                if file_extension in language_extensions[language]:
                    files_per_language[language][file_extension] += 1
    
    # find the language with the maximal amount of files
    max_files = 0
    max_lang = 'Not detected'
    for language in files_per_language:
        if max_files < sum(files_per_language[language].values()):
           max_lang = language
           max_files = sum(files_per_language[language].values())
   
    # as C and C++ share the same extension .c we assume to have a C++
    # project only if at least 2/3 of the files have a C++ extension 
    if 'C++' is max_lang:
        cpp_extensions_ratio = 1 - (files_per_language['C++']['.c'] + files_per_language['C++']['.h']) / \
            sum(files_per_language[language].values())
        if not cpp_extensions_ratio > 2./3.:
             max_lang = 'C'

    # write the result to the report
    report['language'] = max_lang
