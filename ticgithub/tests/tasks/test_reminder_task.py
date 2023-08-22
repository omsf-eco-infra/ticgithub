import pytest
from unittest.mock import Mock
import logging

from datetime import datetime
from functools import partial

from ticgithub.tasks.reminder_task import ReminderTask
from ticgithub.tests.utils import datafile

def _make_issues():
    def _dict_func(label, dct):
        return dct[label]

    no_snooze = partial(_dict_func, dct={'snooze-5-minutes': None,
                                         'snooze-5-hours': None})
    return {
        'pre-delay': Mock(
            number=1,
            is_ticket_issue=True,
            date_created=datetime(2000, 1, 1, 11, 0, 0),
            labels=set(),
            label_added=Mock(side_effect=no_snooze),
        ),
        'delay-expired': Mock(
            number=2,
            is_ticket_issue=True,
            date_created=datetime(2000, 1, 1, 0, 0, 0),
            labels=set(),
            label_added=Mock(side_effect=no_snooze),
        ),
        # 5-minute snooze started at 11am (not in effect at noon)
        'snooze-expired': Mock(
            number=3,
            is_ticket_issue=True,
            date_created=datetime(2000, 1, 1, 0, 0, 0),
            labels={'snooze-5-minutes'},
            label_added=Mock(side_effect=partial(_dict_func, dct={
                'snooze-5-minutes': datetime(2000, 1, 1, 11, 0, 0),
            })),
        ),
        # 5-hour snooze started at 11am (still in effect at noon)
        'snoozed': Mock(
            number=4,
            is_ticket_issue=True,
            date_created=datetime(2000, 1, 1, 0, 0, 0),
            labels={'snooze-5-hours'},
            label_added=Mock(side_effect=partial(_dict_func, dct={
                'snooze-5-hours': datetime(2000, 1, 1, 11, 0, 0),
            })),
        ),
    }


class MockReminder(ReminderTask):
    REMINDER_TYPE = "For Testing"
    DEFAULT_TEMPLATE_FILE = datafile('mockremindertemplate.txt')

    def _get_relevant_issues(self):
        yield from _make_issues().values()

    def _extract_date(self, issue, config):
        return issue.date_created


class TestReminderTask:
    def setup_method(self):
        self.now = datetime(2000, 1, 1, 12, 0, 0)
        bot = Mock(make_comment=Mock())
        inbox = Mock()
        config = {
            'active': True,
            'cron': "0 15 * * * ",
            'email-ticket-only': True,
            'delay': {'hours': 2},
            'snooze-labels': {
                'snooze-5-minutes': {'minutes': 5},
                'snooze-5-hours': {'hours': 5},
            },
            'notify': [],
        }
        team = Mock()
        self.issues = _make_issues()
        self.task = MockReminder(inbox, bot, team, config)
        self.config = self.task._build_config()

    @pytest.mark.parametrize('issue_name', [
        'delay-expired',
        'snooze-expired',
        'snoozed'
    ])
    def test_get_snooze_time(self, issue_name):
        issue = self.issues[issue_name]
        expected = {
            'delay-expired': issue.date_created,
            'snooze-expired': datetime(2000, 1, 1, 11, 5, 0),
            'snoozed': datetime(2000, 1, 1, 16, 0, 0),
        }[issue_name]
        assert self.task._get_snooze_time(issue, self.config) == expected

    @pytest.mark.parametrize('issue_name', [
        'snooze-expired',
        'delay-expired',
    ])
    @pytest.mark.parametrize('dry', [True, False])
    def test_single_issue_check_does_run(self, issue_name, dry, caplog):
        # test of issues where the reminder *should* be posted
        issue = self.issues[issue_name]
        with caplog.at_level(logging.INFO):
            self.task._single_issue_check(issue, self.config, self.now, dry)

        log_messages = "\n".join(rec.message for rec in caplog.records)
        assert "CREATING COMMENT" in log_messages
        assert "COMMENT CONTENTS" in log_messages

        if not dry:
            assert self.task.bot.make_comment.call_count == 1
        else:
            assert self.task.bot.make_comment.call_count == 0

    @pytest.mark.parametrize('issue_name', [
        'snoozed',
        'pre-delay',
    ])
    @pytest.mark.parametrize('dry', [True, False])
    def test_single_issue_check_does_not_run(self, issue_name, dry, caplog):
        # test of issues where the reminder *should not* be posted
        issue = self.issues[issue_name]
        with caplog.at_level(logging.INFO):
            self.task._single_issue_check(issue, self.config, self.now, dry)

        log_messages = "\n".join(rec.message for rec in caplog.records)
        assert "CREATING COMMENT" not in log_messages
        assert "COMMENT CONTENTS" not in log_messages
        assert self.task.bot.make_comment.call_count == 0
