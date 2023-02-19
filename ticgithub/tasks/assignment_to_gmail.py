import logging
import warnings
_logger = logging.getLogger(__name__)

from .task import Task

class AssignmentToGMail(Task):
    CONFIG = 'assignment-to-gmail'

    @staticmethod
    def make_parser():
        parser = Task.make_parser()
        parser.add_argument("issue_number", type=int)
        return parser

    @classmethod
    def inject_config_parameters(cls, config, opts):
        my_config = config['workflows'].get(cls.CONFIG)
        if my_config:
            my_config["issue_number"] = opts.issue_number

        return config, opts

    def _build_config(self):
        return self.config

    def _run(self, config, dry):
        issue_number = config['issue_number']
        _logger.info(f"LOADING ISSUE {issue_number}")
        issue = self.bot.get_issue(issue_number)
        if not issue.is_ticket_issue:
            _logger.info("EXITING: No email ticket associated with "
                         f"issue {issue_number}")
            return

        assignees = set(issue.assignees)
        ghuser_to_gmail_label = {
            mem.github: mem.label for mem in self.team
        }

        # figure out who isn't on the team
        non_team = assignees - set(ghuser_to_gmail_label)
        if non_team:
            warnings.warn("No GMail labels for the following assignees: "
                          f"{non_team}")

        labels_to_assign = [
            ghuser_to_gmail_label[user] for user in assignees - non_team
        ]
        _logger.info(f"FOR TICKET '{issue.unique_id}' ASSIGNING LABELS "
                     f"{labels_to_assign}")
        if not dry:
            self.inbox.set_labels(issue.unique_id, labels_to_assign)


if __name__ == "__main__":
    AssignmentToGMail.run_cli()
