class ScrabTask():

    """
    Base class of all scrab tasks

    __DO NOT__ inherit! Use a dedicated class like GitTask!

    :param    name:         The name of the scrab task
    :param    kind:         The kind of the scrab task
    :param    version:      The version of the scrab task
    :param    parameter:    The parameter for the scrab task
    :param    global_args:  The global arguments global arguments that may
                            be interesting for the scrab task
    """

    def __init__(self, name, kind, version, parameter, global_args):
        self.name = name
        self.kind = kind
        self.version = version
        self._parameter = parameter
        self._global_args = global_args


class GitTask(ScrabTask):

    """
    Base class of all scrab tasks that want to analyse a git project.
    It is important to note, that this task is intended to collect git data only
    if you wish to collect data about files or even search in them use the
    FileTask class as base class

    :param    name:         The name of the scrab task
    :param    version:      The version of the scrab task
    :param    parameter:    The parameter for the scrab task
    :param    global_args:  The global arguments global arguments that may be
                            interesting for the scrab task
    """

    def __init__(self, name, version, parameter, global_args):
        super(GitTask, self).__init__(name, 'git', version, parameter,
                                      global_args)

    def scrab(self, project):
        """
        Function that will be called to analyse the given project

        __Override this method and do not call it!__

        :param    project:  The project that the scrab task shall analyse

        :returns: Report that contains all scrabbed information
        """
        assert False, "You have to implement this function"


class FileTask(ScrabTask):

    """
    Base class of all scrab tasks that want to analyse a the files of a project.

    It is important to note, that this task is the most difficult one to get
    right. The scrab and merge methods are called by multiple threads leading to
    race conditions if they write to shared memory. Thus one should only read
    from the instances attributes and refrain from modifying the state.

    The instance should be thought about as read only data storage

    :param    name:         The name of the scrab task
    :param    version:      The version of the scrab task
    :param    parameter:    The parameter for the scrab task
    :param    global_args:  The global arguments global arguments that may be
                            interesting for the scrab task
    """

    def __init__(self, name, version,  parameter, global_args):
        super(FileTask, self).__init__(name, 'git', version, parameter,
                                       global_args)

    def scrab(self, project, filepath, file):
        """
        Function that will be called to analyse the given project file.

        __This method is called by multiple threads *simultaneously*__
        __Do NOT modify the instances state or race conditions will arise!__

        __Override this method and do not call it!__

        :param    project:   The project that the scrab task shall analyse
        :param    filepath:  The filepath to the file that can be analysed
        :param    file:      The file as string that can be analysed

        :returns: Report that contains the scrabbed information of *this* file
        """
        assert False, "You have to implement this function"

    def merge(self, first, second):
        """
        Merges two partial reports.

        __This method is called by multiple threads *simultaneously*__
        __Do NOT modify the instances state or race conditions will arise!__

        __Override this method and do not call it!__

        :param    first:   The first report (all reports so far)
        :param    second:  The second report (the new report that has to be
                           merged)

        :returns: Merged report that contains the results from the first and
                  second one
        """
        assert False, "You have to implement this function"

    def finish(self, report):
        """
        Last finishing touches may be done here.

        :param    report:  The complete report this task created

        :returns: Report that contains all scrabbed information
        """
        return report


class ReportTask(ScrabTask):

    """
    Base class of all scrab tasks that want to analyse the final report.

    :param    name:         The name of the scrab task
    :param    version:      The version of the scrab task
    :param    parameter:    The parameter for the scrab task
    :param    global_args:  The global arguments global arguments that may be
                            interesting for the scrab task
    """

    def __init__(self, name, version,  parameter, global_args):
        super(ReportTask, self).__init__(name, 'git', version, parameter,
                                         global_args)

    def scrab(self, report):
        """
        Function that will be called to analyse the complete report

        __Override this method and do not call it!__

        :param    report:  The report that the scrab task shall analyse

        :returns: Report that contains all scrabbed information
        """
        assert False, "You have to implement this function"
