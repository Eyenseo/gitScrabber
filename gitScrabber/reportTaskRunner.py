class ReportTaskRunner:
    """docstring for ReportTaskRunner"""  # TODO

    def __init__(self, task_yaml, report_yaml, scrabTaskManager):
        super(ReportTaskRunner, self).__init__()
        self.task_yaml = task_yaml
        self.report_yaml = report_yaml
        self.scrabTaskManager = scrabTaskManager

    def run_tasks(self):
        for task_name in self.task_yaml['tasks']['report']:
            scrabTask = self.scrabTaskManager.get_task(task_name)
            scrabTask['function'](self.report_yaml)
