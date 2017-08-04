import os

name = "languageDetector"
version = "1.0.1"


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


def __get_language_extensions():
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


def __get_files_per_language():
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


def __count_language_files(project_dir):
    # dictionary containing the common file extensions
    # for each of the languages
    language_extensions = __get_language_extensions()

    # count the files that have an extension of one of the languages
    files_per_language = __get_files_per_language()

    # walk through all files in the project and count extensions
    for dirpath, dirnames, filenames in os.walk(project_dir):
        for file in filenames:
            filename, file_extension = os.path.splitext(file)
            for language in language_extensions:
                if file_extension in language_extensions[language]:
                    files_per_language[language][file_extension] += 1

    __decide_h_extension(files_per_language)

    return files_per_language


def __decide_h_extension(files_per_language):
    """
    Decides which language 'owns' how many .h files

    :param    files_per_language:  Dict containing the files per extension per
                                   language
    """
    h_files = files_per_language['C']['.h']
    if h_files > 0:
        c_files = (sum(files_per_language['C'].values()) - h_files)
        cpp_files = (sum(files_per_language['C++'].values())
                     - h_files
                     - files_per_language['C++']['.c'])
        oc_files = (sum(files_per_language['Objective-C'].values()) - h_files)
        lang_fiels = c_files + cpp_files + oc_files

        # Header only libraries are 'common' in C and C++
        # the benefit of doubt goes to C
        if lang_fiels == 0:
            files_per_language['C']['.h'] = 1
            files_per_language['C++']['.h'] = 0
            files_per_language['Objective-C']['.h'] = 0
        else:
            files_per_language['C']['.h'] = (h_files *
                                             c_files / lang_fiels)
            files_per_language['C++']['.h'] = (h_files *
                                               cpp_files / lang_fiels)
            files_per_language['Objective-C']['.h'] = (h_files *
                                                       oc_files / lang_fiels)


def __calculate_main_language(files_per_language):
    # find the language with the maximal amount of files
    max_files = 0
    max_lang = 'Not detected'

    for language in files_per_language:
        lang_fiels = sum(files_per_language[language].values())
        if max_files < lang_fiels:
            max_lang = language
            max_files = lang_fiels

    return max_lang


def __calculate_used_languages(files_per_language, main_language):
    languages = {}

    for language, _ in files_per_language.items():
        total_files = sum(files_per_language[language].values())

        if total_files > 0:
            languages[language] = total_files

    return sorted(languages, key=languages.get, reverse=True)


def languageDetector(project_report, project, task_params,  global_args):
    """
    Tries to detect the programming language of a library based on the file
    extension

    :param    project_report:  The project report so far - __DO NOT MODIFY__
    :param    project:         The project
    :param    task_params:     Parameter given explicitly for this task, for all
                               projects, defined in the task.yaml
    :param    global_args:     Arguments that will be passed to all tasks. They
                               _might_ contain something that is useful for the
                               task, but the task has to check if it is _there_
                               as these are user provided. If they are needed to
                               work that check should happen in the argHandler.

    :returns: The report of this task as a dictionary
    """
    report = {}
    files_per_language = __count_language_files(project['location'])
    main_language = __calculate_main_language(files_per_language)

    # write the result to the report
    report['main_language'] = main_language
    report['languages'] = __calculate_used_languages(
        files_per_language, main_language)

    return report
