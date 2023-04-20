import itertools
import string
from datetime import timedelta, datetime
from email.mime.text import MIMEText

import logging
_logger = logging.getLogger(__name__)

from ..issues import Issue, NoIssue
from .task import Task
from ..utils.datafiles import text_template


# FILTERS
#
# Filters are designed to identify emails that should not be made into GitHub issues.
# The filter returns a Callable[[Message], bool]. This callable should return True if
# the Message should be excluded from the messages to turn into issues.

def _log_emails(emails):
    for email in emails:
        _logger.debug(f"Subject: {email.subject}")
        _logger.debug(f"From: {email.get('From')}")
        yield email

def message_from_bot(inbox, bot, team, config):
    def bot_filter_inner(msg):
        _logger.debug("Checking message for bot senders")
        if bot.smtp and bot.smtp.user in msg.get("From"):
            _logger.debug("Filtered bot sender")
            return True
        else:
            return False

    return bot_filter_inner

def message_from_team_not_to(inbox, bot, team, config):
    def team_filter_inner(msg):
        _logger.debug("Checking message for team senders")
        is_team = any(mem.email in msg.get("From") for mem in team)
        is_to = inbox.user in msg.get("To")
        if is_team and not is_to:
            _logger.debug("Filtered team sender")
            return True
        else:
            return False

    return team_filter_inner

def message_from_specified(inbox, bot, team, config):
    def message_from_specified_inner(msg):
        _logger.debug("Checking message for specified senders")
        for sender in config['senders']:
            if sender in msg.get("From"):
                _logger.debug("Filtered specified sender")
                return True
            else:
                return False

    return message_from_specified_inner


def _reply_template(config):
    default_filename = text_template("email_reply.txt")
    template_filename = config.get('template', default_filename)
    with open(template_filename) as f:
        template_str = f.read()
    reply_template = string.Template(template_str)

    return reply_template


class EmailsToIssues(Task):
    """Task to create GitHub issue from emails.
    """
    CONFIG = "emails-to-issues"
    FILTERS = {
        'bot': message_from_bot,
        'team': message_from_team_not_to,
        'omit-senders': message_from_specified,
    }

    def _build_filters(self, filt_config):
        filters = []
        for filt in filt_config:
            if not filt.get("active", True):
                continue
            filter_builder = self.FILTERS[filt['name']]
            new_filter = filter_builder(self.inbox, self.bot, self.team, filt)
            filters.append(new_filter)
        return filters

    def _build_config(self):
        config_dict = self.config
        filter_config = config_dict.get("filters")
        filters = self._build_filters(filter_config)
        recent = timedelta(**config_dict.get("recent", {'hours': 48}))

        config = {
            'filters': filters,
            'recent': recent,
        }

        if reply_config := config_dict.get("reply-inbox"):
            if reply_config.get("active", True):
                config.update({'reply_template': _reply_template(reply_config)})

        return config

    def single_email_to_issue(self, msg, dry):
        # create the issue
        contents = Issue.issue_body_from_message(msg)
        _logger.info(f"CREATING ISSUE\ntitle: {msg.subject}:\n{contents}")

        if not dry:
            issue = self.bot.create_issue(msg.subject, contents)
            _logger.info(f"CREATED ISSUE {issue.number}")
        else:
            # used in dry run only
            issue = NoIssue()

        return issue

    def send_reply_email(self, orig, issue, reply_template, dry):
        content = reply_template.substitute(
            GITHUB_URL=issue.html_url,
        )
        subj = orig.subject
        if not subj[:4].upper() == "RE: ":
            subj = "RE: " + subj

        reply_email = MIMEText(content)
        reply_email["Subject"] = subj
        reply_email["To"] = self.inbox.user
        reply_email["From"] = self.bot.smtp.user
        reply_email["In-Reply-To"] = orig.get("Message-ID")
        if thread_topic := orig.get("Thread-Topic"):  # 🖕 Microsoft
            reply_email["Thread-Topic"] = thread_topic

        _logger.info(f"SENDING EMAIL:\n{reply_email.as_string()}")
        if not dry:
            self.bot.smtp.sendmail(reply_email, [self.inbox.user])

    def _run(self, config, dry):
        _logger.debug(f"CONFIG: {config}")
        since = datetime.now() - config['recent']
        emails = self.inbox.get_emails(since=since)
        filtered = itertools.filterfalse(
            lambda x: any(f(x) for f in config['filters']),
            _log_emails(emails)
        )


        issues = self.bot.get_all_email_ticket_issues()
        id_to_message = {msg.unique_id: msg for msg in filtered}
        id_to_issue = {iss.unique_id: iss for iss in issues}

        ids_to_add = set(id_to_message) - set(id_to_issue)
        _logger.info(f"Downloaded {len(emails)} emails")
        _logger.info(f"Kept {len(id_to_message)} after filtering")
        _logger.info(f"Adding {len(ids_to_add)} new messages")
        for id_ in ids_to_add:
            msg = id_to_message[id_]
            issue = self.single_email_to_issue(msg, dry)
            if template := config.get('reply_template'):
                if not self.bot.smtp:
                    # TODO: fail faster on this; validate config
                    raise RuntimeError(
                        "SMTP must be defined for bot to send replies."
                    )

                self.send_reply_email(msg, issue, template, dry)

if __name__ == "__main__":
    EmailsToIssues.run_cli()
