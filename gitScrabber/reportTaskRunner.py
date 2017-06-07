class ReportTaskRunner:
    """
    The ReportTaskRunner executes the scrab tasks specified in the task.yaml
    file

    :param  tasks:             The task configuration
    :param  report:            The report to analyse and write into
    :param  scrabTaskManager:  The scrab task manager
    """

    def __init__(self, tasks, report, scrabTaskManager):
        super(ReportTaskRunner, self).__init__()
        self.__tasks = tasks
        self.__report = report
        self.__scrabTaskManager = scrabTaskManager

    def run_tasks(self):
        """
        Executes the report scrab tasks sequentially
        """
        for task_name in self.__tasks:
            scrabTask = self.__scrabTaskManager.get_task(task_name)
            scrabTask['function'](self.__report)
