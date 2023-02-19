# Gmail-specific extensions
import shlex
import re

from .inbox import Message, Inbox

__all__ = ["GMailInbox", "GMessage"]

LABEL_PATTERN = re.compile(".*X-GM-LABELS \((?P<labels>[^)]*)\)")
MSGID_PATTERN = re.compile(".*X-GM-MSGID (?P<msgid>[0-9]+)")


def extract_from_pattern(string, pattern, pattern_name):
    if isinstance(string, bytes):
        string = str(string, 'utf-8')

    if match := pattern.match(string):
        found = match.group(pattern_name)
    else:
        found = ""

    return found


class GMessage(Message):
    @property
    def unique_id(self):
        return extract_from_pattern(self._extra, MSGID_PATTERN, "msgid")

    @property
    def labels(self):
        label_str = extract_from_pattern(self._extra, LABEL_PATTERN,
                                         "labels")
        return shlex.split(label_str)


class GMailInbox(Inbox):
    FETCH_STR = "(RFC822 X-GM-LABELS X-GM-MSGID)"
    MESSAGE_CLASS = GMessage
    TYPE = "gmail"

    def _toggle_labels(self, gm_msg_id, labels, direction):
        if direction not in ("+", "-"):
            raise ValueError(f"direction must be '+' or '-', not "
                             f"{direction}")

        with self.connection() as imap:
            labels_arg = f"({' '.join(labels)})"
            typ, data = imap.uid("SEARCH", f"X-GM-MSGID {gm_msg_id}")
            num = str(data[0], 'utf-8')
            store_args = f"{num} {direction}X-GM-LABELS {labels_arg}"
            imap.uid("STORE", store_args)

    def _add_labels(self, gm_msg_id, labels):
        return _toggle_labels(gm_msg_id, labels, "+")

    def _remove_labels(self, gm_msg_id, labels):
        return _toggle_labels(gm_msg_id, labels, "-")

    def set_labels(self, gm_msg_id, labels):
        ...  # get existing labels; get the set diffs; add and remove
