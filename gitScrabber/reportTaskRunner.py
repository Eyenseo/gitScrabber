class ReportTaskRunner:
    """
    The ReportTaskRunner executes the scrab tasks specified in the task.yaml
    file

    :param  tasks:             The task configuration
    :param  report:            The report to analyse and write into
    :param  global_args:       Arguments that will be passed to all tasks. They
                               _might_ contain something that is useful for the
                               task, but the task has to check if it is _there_
                               as these are user provided. If they are needed to
                               work that check should happen in the argHandler.
    :param  scrabTaskManager:  The scrab task manager
    """

    def __init__(self, tasks, report, global_args, scrabTaskManager):
        super(ReportTaskRunner, self).__init__()
        self.__tasks = tasks
        self.__report = report
        self.__global_args = global_args
        self.__scrabTaskManager = scrabTaskManager

    def run_tasks(self):
        """
        Executes the report scrab tasks sequentially
        """
        for task in self.__tasks:
            meta_task = self.__scrabTaskManager.get_task(task.name)
            scrab_task = meta_task.construct(task.parameter,
                                             self.__global_args)
            self.__report = scrab_task.scrab(self.__report)
