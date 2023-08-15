import re

# consider https://github.com/shinnn/github-username-regex
def at_mention_cleaner(content):
    regex = re.compile("^(?P<pre>[^A-Za-z0-9]?)@(?P<post>[A-Za-z0-9])")
    content = re.sub(regex, "\g<pre>@<!-- -->\g<post>", content)
    return content

DEFAULT_CLEANERS = (
    at_mention_cleaner,
)

def clean_content(content, cleaners=DEFAULT_CLEANERS):
    for cleaner in cleaners:
        content = cleaner(content)

    return content


