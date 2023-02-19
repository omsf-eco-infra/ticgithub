from .reminder_task import ReminderTask

from ..utils.datafiles import text_template

class UnassignedReminder(ReminderTask):
    REMINDER_TYPE = "Unassigned issue"
    DEFAULT_TEMPLATE_FILE = text_template("unassigned.txt")
    CONFIG = "unassigned-reminder"

    def _get_relevant_issues(self):
        # unassigned issues
        return self.bot.get_unassigned_issues()

    def _extract_date(self, issue, config):
        # issue creation date
        return issue.date_created


if __name__ == "__main__":
    UnassignedReminder.run_cli()
