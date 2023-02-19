import string
from datetime import datetime, timedelta

import yaml

import logging
_logger = logging.getLogger(__name__)

from .task import Task

class ReminderTask(Task):
    REMINDER_TYPE = None
    DEFAULT_TEMPLATE_FILE = None

    def _build_config(self):
        config = dict(self.config)
        config['delay'] = timedelta(**config['delay'])
        template_file_name = config.get('template',
                                        self.DEFAULT_TEMPLATE_FILE)
        with open(template_file_name, 'r') as f:
            config['template'] = string.Template(f.read())

        return config

    def craft_reminder_comment(self, template, notify):
        frontmatter = yaml.dump({"REMINDER": self.REMINDER_TYPE})
        if notify:
            notification = " ".join(f"@{user}" for user in notify)
            notification += "\n\n"
        else:
            notification = ""

        main_content = template.substitute()  # TODO: add things here

        body = frontmatter + "\n---\n\n" + notification + main_content
        return body

    def _get_relevant_issues(self):
        raise NotImplementedError()

    def _extract_date(self, issue, config):
        raise NotImplementedError()

    def _single_issue_check(self, issue, config, latest_date, dry):
        _logger.debug(f"CHECKING ISSUE {issue.number}")
        if self._extract_date(issue, config) < latest_date:
            _logger.info(f"CREATING COMMENT FOR ISSUE {issue.number}")
            comment = self.craft_reminder_comment(
                template=config['template'],
                notify=config['notify']
            )
            _logger.info("COMMENT CONTENTS:\n" + comment)
            if not dry:
                self.bot.create_comment(issue.number, comment)

    def get_relevant_issues(self):
        issues = self._get_relevant_issues()
        if self.config['email-ticket-only']:
            issues = (iss for iss in issues if iss.is_ticket_issue)
        return issues

    def _run(self, config, dry):
        latest_date = datetime.now() - config['delay']
        for issue in self.get_relevant_issues():
            self._single_issue_check(issue, config, latest_date, dry)
