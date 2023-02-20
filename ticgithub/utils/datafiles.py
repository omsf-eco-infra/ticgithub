from importlib.resources import files


def workflow_template(filename):
    return files('ticgithub.data.workflows') / filename


def text_template(filename):
    return files('ticgithub.data.templates') / filename


DEFAULT_BUILD_CONFIG = files('ticgithub.data') / "build_config.yml"
