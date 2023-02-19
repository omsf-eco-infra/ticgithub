import os
import warnings

import github

from .issues import Issue, NonTicketIssueError

__all__ = ["SMTP", "Bot"]

class SMTP:
    def __init__(self, user, host, secret, port=465):
        self.user = user
        self.host = host
        self.secret = secret
        self.port = port

    def sendmail(self, email, recipients):
        with smtplib.SMTP_SSL(self.host, self.port) as smtp:
            smtp.login(user, os.environ.get(self.secret))
            smtp.sendmail(self.user, recipients, email.as_string())

    def __repr__(self):
        return (f"{self.__class__.__name__}('{self.user}:"
                f"{self.port}")


class Bot:
    def __init__(self, token_secret, repo, smtp=None):
        self.token_secret = token_secret
        self.reponame = repo
        self._github = None
        self.smtp = smtp

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.reponame}', {self.smtp})"

    @classmethod
    def from_config(cls, config):
        if smtp_config := config.get('sendmail'):
            smtp = SMTP(**smtp_config)
        else:
            smtp = None

        return cls(token_secret=config['token_name'],
                   repo=config['repo'],
                   smtp=smtp)

    @property
    def repo(self):
        if self._github is None:
            self._github = github.Github(os.environ[self.token_secret])
        return self._github.get_repo(self.reponame)

    def create_issue(self, title, content):
        return Issue(self.repo.create_issue(title, content))

    def get_issue(self, issue_num):
        return Issue(self.repo.get_issue(issue_num))

    def make_comment(self, issue_num, content):
        issue = self.repo.get_issue(issue_num)
        issue.create_comment(content)

    def get_unassigned_issues(self):
        return (
            Issue(iss)
            for iss in self.repo.get_issues(state="open")
            if not iss.assignees
        )

    def get_open_issues(self):
        return (Issue(iss) for iss in self.repo.get_issues(state="open"))

    def get_all_issues(self):
        return (Issue(iss) for iss in self.repo.get_issues(state="all"))

    def get_all_email_ticket_issues(self, nonticket="warn"):
        for iss in self.get_all_issues():
            try:
                iss.unique_id
            except NonTicketIssueError as e:
                if nonticket == "warn":
                    warnings.warn(str(e))
                elif nonticket == "error":
                    raise
            else:
                yield iss
