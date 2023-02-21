import os
import collections
import contextlib

import imaplib
import email
from email.utils import parsedate_to_datetime
from email.header import decode_header
from email.contentmanager import raw_data_manager

__all__ = ["Message", "Inbox"]

class Message:
    def __init__(self, extra, contents):
        self._extra = extra
        self._msg = email.message_from_bytes(contents)

    @property
    def unique_id(self):
        return self._msg["Message-ID"]

    @property
    def date(self):
        return parsedate_to_datetime(self._msg["Date"])

    @property
    def subject(self):
        output, encoding = decode_header(self._msg['subject'])[0]
        if isinstance(output, bytes):
            output = output.decode(encoding)

        return output

    def get(self, key):
        return self._msg.get(key)

    def _group_messages_by_content_type(self):
        messages = collections.defaultdict(list)
        for m in self._msg.walk():
            messages[m.get_content_type()].append(m)

        return dict(messages)

    @staticmethod
    def _get_desired_message(messages_by_content_type, type_order):
        for content_type in type_order:
            desired_messages = messages_by_content_type.get(content_type)
            if desired_messages:
                break

        return desired_messages[0]  # for now take the first one? Don't know

    def get_content(self, content_type_order=None):
        if content_type_order is None:
            content_type_order = ["text/plain", "text/html"]

        messages_by_content_type = self._group_messages_by_content_type()
        message = self._get_desired_message(messages_by_content_type,
                                            content_type_order)

        return raw_data_manager.get_content(message)


class Inbox:
    MESSAGE_CLASS = Message
    FETCH_STR = "RFC822"
    TYPE = "imap"

    def __init__(
        self,
        host,
        user,
        secret,
        mailbox="INBOX",
        ssl_port=993,
    ):
        self.host = host
        self.user = user
        self.secret = secret
        self.mailbox = mailbox
        self.ssl_port = ssl_port
        self.progress = lambda x: x

    def __repr__(self):
        return (f"{self.__class__.__name__}('{self.user}:"
                f"{self.ssl_port}/{self.mailbox}')")

    @classmethod
    def from_config(cls, config):
        kwargs = {k: v for k, v in config.items() if k != "type"}
        return cls(**kwargs)

    @contextlib.contextmanager
    def connection(self):
        """Get a connection to the IMAP server (use as context manager)."""
        password = os.environ.get(self.secret)
        imap = imaplib.IMAP4_SSL(self.host, port=self.ssl_port)
        imap.login(self.user, password)
        imap.select(self.mailbox)
        yield imap
        imap.logout()

    def _create_message(self, fetched):
        return self.MESSAGE_CLASS(*fetched[1][0])

    def _get_emails(self, search_string="ALL"):
        with self.connection() as imap:
            typ, data = imap.search(None, search_string)
            fetch_msgs = [
                imap.fetch(num, self.FETCH_STR)
                for num in self.progress(data[0].split())
            ]

        msgs = [self._create_message(m) for m in fetch_msgs]
        return msgs

    def get_emails(self, since=None):
        if since is None:
            search_string = "ALL"
        else:
            since_date = since.strftime("%d-%b-%Y")
            search_string = f"(SINCE {since_date})"
        return self._get_emails(search_string)

    def get_email(self, unique_id):
        for email in self.get_emails():
            if email.unique_id == unique_id:
                return email
