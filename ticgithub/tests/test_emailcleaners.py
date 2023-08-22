import pytest

from ticgithub.emailcleaners import *


@pytest.mark.parametrize('unclean, cleaned', [
    ("@dwhswenson", "@<!-- -->dwhswenson"),
    ("/@dwhswenson", "/@<!-- -->dwhswenson"),
    ("-@dwhswenson", "-@<!-- -->dwhswenson"),
    ("-@dwhswenson", "-@<!-- -->dwhswenson"),
    (".@dwhswenson", ".@<!-- -->dwhswenson"),
    ("!@dwhswenson", "!@<!-- -->dwhswenson"),
    ("1@dwhswenson", "1@dwhswenson"),
    ("a@dwhswenson", "a@dwhswenson"),
    ("foo@dwhswenson", "foo@dwhswenson"),
    ("blah!@dwhswenson", "blah!@<!-- -->dwhswenson"),
    (" @dwhswenson", " @<!-- -->dwhswenson"),
])
def test_at_mention_cleaner(unclean, cleaned):
    assert at_mention_cleaner(unclean) == cleaned
