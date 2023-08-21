from importlib import resources

def datafile(filepath):
    return resources.files('ticgithub.tests.data').joinpath(filepath)

