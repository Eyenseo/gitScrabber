from packaging import version


class ProjectTaskRunner:
    """
    The ProjectTaskRunner is responsible for executing tasks that scrab at the
    git repos and archives. These tasks are meant to gather data, not
    necessarily interpret it. The interpretation is better left to the report
    scrab task.
    Each ProjectTaskRunner is responsible for a single project and will create
    the portion of the final report that contains the information of this
    project

    :param  project:           The project the scrab tasks run for
    :param  tasks:             The tasks that will run for the project
    :param  old_tasks:         The old tasks that were used to generate old_data
    :param  old_data:          The old data that was produced in a previous run
                               with old_tasks
    :param  global_args:       Arguments that will be passed to all tasks. They
                               _might_ contain something that is useful for the
                               task, but the task has to check if it is _there_
                               as these are user provided. If they are needed to
                               work that check should happen in the argHandler.
    :param  scrabTaskManager:  The ScrabTaskManager
    """

    def __init__(self, project, tasks, old_tasks, old_data,
                 global_args, scrabTaskManager):
        self.__project = project
        self.__tasks = tasks
        self.__old_tasks = old_tasks
        self.__old_data = old_data
        self.__global_args = global_args
        self.__scrabTaskManager = scrabTaskManager

        self.__project_to_task_mapping = {
            'archive': ['archive'],
            'git': ['git', 'archive']
        }

    def __changed_task(self, scrabTask):
        """
        Checks weather the scrab task has to be rerun based on an old report
        and the scab task versions

        :param    scrabTask:  The scrab task to check against

        :returns: True if the scrab task has to rerun False otherwise
        """
        return(
            not self.__old_tasks
            or scrabTask.name not in self.__old_tasks
            or version.parse(self.__old_tasks[scrabTask.name])
            != version.parse(scrabTask.version)
        )

    def run_tasks(self):
        """
        This function is responsible to ensure that the source files are
        present. It also decides weather the scrab tasks have to run again based
        in their version and the version mentioned in the old report as well as
        if the source files have changed

        :returns: The sub-report containing all project information of this
                  project
        """
        report = {}
        tasks_to_do = self.__project_to_task_mapping[self.__project.kind]
        task_changed = False

        for task in self.__tasks:
            scrabTask = self.__scrabTaskManager.get_task(task.name)

            if scrabTask.kind not in tasks_to_do:
                continue

            if not task_changed:
                task_changed = self.__changed_task(scrabTask)

            if self.__project.updated or task_changed:
                report[task.name] = scrabTask.function(report,
                                                       self.__project,
                                                       task.parameter,
                                                       self.__global_args)
            elif self.__old_data and task.name in self.__old_data:
                report[task.name] = self.__old_data[task.name]

        return report
