from importlib import resources
import os

import pytest


def datafile(filepath):
    return resources.files('ticgithub.tests.data').joinpath(filepath)


def get_envvars_or_skip(*envvars):
    vals = [os.environ.get(var) for var in envvars]
    vals = []
    missing = []
    for var in envvars:
        if val := os.environ.get(var):
            vals.append(val)
        else:
            missing.append(var)

    if missing:
        pytest.skip("Missing environment variables: "
                    + ", ".join(f"${var}" for var in missing))

    return vals
