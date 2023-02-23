from .reminder_task import ReminderTask
from ..utils.datafiles import text_template

class UnclosedReminder(ReminderTask):
    REMINDER_TYPE = "Issue assigned but not closed"
    DEFAULT_TEMPLATE_FILE = text_template("unclosed.txt")
    CONFIG = "unclosed-reminder"

    def _get_relevant_issues(self):
        for issue in self.bot.get_open_issues():
            if issue.assignees:
                yield issue

    def _extract_date(self, issue, config):
        return issue.date_last_assigned


if __name__ == "__main__":
    UnclosedReminder.run_cli()
