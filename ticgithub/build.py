import pathlib
import string

import yaml

from .utils.datafiles import workflow_template, DEFAULT_BUILD_CONFIG

import logging
_logger = logging.getLogger(__name__)


def get_workflow_template(template_name):
    path = pathlib.Path(template_name)
    if not path.exists():
        path = workflow_template(template_name)
        if not path.exists():
            raise RuntimeError("Unable to find workflow template "
                               f"{template_name}.")

    with open(path) as f:
        template = string.Template(f.read())

    return template


def build_substitutions(ticgithub_dict, builder_dict, config):
    dry = " --dry" if ticgithub_dict.get("force-dry") else ""
    if suffix := ticgithub_dict.get("suffix", ""):
        suffix = "-" + suffix

    default_install = "python -m pip install ticgithub"
    install = ticgithub_dict.get("install", default_install)

    name = builder_dict['config-name']

    ticgithub_sub = {
        "INSTALL_CMD": install,
        "SUFFIX": suffix,
        "DRY": dry,
    }

    workflow_builder_sub = {
        "NAME": name,
        "RUN_CMD": builder_dict['run-command'],
    }

    secrets = {
        "PAT": config['config']['bot']['token_name'],
        "INBOX": config['config']['inbox']['secret'],
    }
    sendmail_cfg = config['config']['bot'].get('sendmail', {})
    if sendmail_secret := sendmail_cfg.get('secret'):
        secrets["SENDMAIL"] = sendmail_secret

    build_params = builder_dict.get('build-params', {})
    workflow_build_params_sub = {
        value: config['workflows'][name][key]
        for key, value in build_params.items()
    }

    substitutions = dict(**ticgithub_sub, **workflow_builder_sub, **secrets,
                         **workflow_build_params_sub)
    return substitutions

def build_workflow(ticgithub_dict, builder_dict, config, dry):
    template = get_workflow_template(builder_dict['template'])
    substitutions = build_substitutions(ticgithub_dict, builder_dict,
                                        config)
    filename = substitutions["NAME"] + substitutions["SUFFIX"] + ".yml"
    directory = pathlib.Path(ticgithub_dict['install-path'])
    contents = template.substitute(substitutions)
    _logger.info(f"WRITING TO: {directory / filename}")
    _logger.info(f"Contents:\n{contents}")
    if not dry:
        directory.mkdir(parents=True, exist_ok=True)
        with open(directory / filename, mode="w") as f:
            f.write(contents)

def build(build_config, config, dry):
    ticgithub_dict = build_config.get('ticgithub', {})
    name_to_build_config = {builder['config-name']: builder
                            for builder in build_config['builders']}
    for workflow in config['workflows']:
        builder_dict = name_to_build_config[workflow]
        build_workflow(ticgithub_dict, builder_dict, config, dry)


def make_parser():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry', action="store_true", default=False)
    parser.add_argument('-c', '--config', type=str,
                        default=".ticgithub.yml")
    parser.add_argument('--build-config', type=str, default=None)
    parser.add_argument('--loglevel', type=str, default="WARNING")
    return parser


if __name__ == "__main__":
    parser = make_parser()
    opts = parser.parse_args()
    logging.basicConfig(level=getattr(logging, opts.loglevel))
    if not (build_config_file := opts.build_config):
        build_config_file = DEFAULT_BUILD_CONFIG
    with open(build_config_file) as f:
        build_config = yaml.load(f, Loader=yaml.FullLoader)

    with open(opts.config) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    build(build_config, config, opts.dry)
