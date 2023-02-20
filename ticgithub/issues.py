import yaml
from datetime import datetime

import github

class NonTicketIssueError(Exception):
    pass

class Issue:
    """
    Simple wrapper around github.Issue to define our supported API.
    """
    def __init__(self, issue: github.Issue):
        self._issue = issue

    @staticmethod
    def issue_body_from_message(message):
        frontmatter = {
            'ticket_id': message.unique_id,
            'From': message.get("From"),
            'Date': str(message.date),
            'Subject': message.subject,
        }
        yaml_part = yaml.dump(frontmatter)
        return yaml_part + "\n---\n" + message.get_content()

    @staticmethod
    def _get_frontmatter(body):
        for frontmatter in yaml.load_all(body, Loader=yaml.FullLoader):
            break
        if 'Date' in frontmatter:
            frontmatter['Date'] = datetime.fromisoformat(frontmatter['Date'])
        return frontmatter

    @staticmethod
    def _unique_id_from_body(body):
        return Issue._get_frontmatter(body)['ticket_id']

    @property
    def is_ticket_issue(self):
        try:
            self.unique_id
        except NonTicketIssueError:
            return False
        else:
            return True

    @property
    def unique_id(self):
        try:
            return self._unique_id_from_body(self._issue.body)
        except (yaml.YAMLError, KeyError):
            raise NonTicketIssueError(
                f"Issue {self.number} does not have a ticket ID"
            )

    @property
    def date_created(self):
        return self._issue.created_at

    @property
    def date_last_assigned(self):
        assigns = [
            event for event in self._issue.get_timeline()
            if event.event == "assigned"
        ]
        last_assignment = sorted(assigns, key=lambda x: x.created_at)[-1]
        return last_assignment.created_at

    @property
    def number(self):
        return self._issue.number

    @property
    def html_url(self):
        return self._issue.html_url

    @property
    def title(self):
        return self._issue.title

    @property
    def assignees(self):
        return (assignee.login for assignee in self._issue.assignees)


class NoIssue(Issue):
    """
    Special case to provide an :class:`.Issue` for dry runs.
    """
    def __init__(self):
        pass

    @property
    def unique_id(self):
        return "<UNKNOWN ID>"

    @property
    def number(self):
        return 0

    @property
    def html_url(self):
        return "<UNKNOWN URL>"

    @property
    def title(self):
        return "<UNKNOWN TITLE>"

    @property
    def assignees(self):
        return []
