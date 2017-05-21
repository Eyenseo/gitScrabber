class ReportTaskRunner:

    """
    The ReportTaskRunner executes the scrab tasks specified in the task.yaml
    file

    :param  task_yaml:         The task configuration
    :param  report_yaml:       The report to analyse and write into
    :param  scrabTaskManager:  The scrab task manager
    """

    def __init__(self, task_yaml, report_yaml, scrabTaskManager):
        super(ReportTaskRunner, self).__init__()
        self.task_yaml = task_yaml
        self.report_yaml = report_yaml
        self.scrabTaskManager = scrabTaskManager

    def run_tasks(self):
        """
        Executes the report scrab tasks sequentially
        """
        for task_name in self.task_yaml['tasks']['report']:
            scrabTask = self.scrabTaskManager.get_task(task_name)
            scrabTask['function'](self.report_yaml)
