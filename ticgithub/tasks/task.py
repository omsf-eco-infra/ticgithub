import logging
_logger = logging.getLogger("__name__")

import yaml

from ..inbox import Inbox
from ..gmail import GMailInbox
from ..bot import Bot
from ..team import TeamMember

BOXTYPE_DISPATCH = {
    'gmail': GMailInbox
}

class Task:
    CONFIG = None
    def __init__(self, inbox, bot, team, config):
        self.inbox = inbox
        self.bot = bot
        self.team = team
        self.config = config

    @staticmethod
    def make_parser():
        _logger.debug("building parser")
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--dry', action="store_true", default=False)
        parser.add_argument('-c', '--config', type=str,
                            default=".ticgithub.yml")
        parser.add_argument('--loglevel', type=str, default="INFO")
        return parser

    @classmethod
    def inject_config_parameters(cls, config, opts):
        return config, opts

    @staticmethod
    def use_parser(parser, args=None):
        _logger.debug("using parser")
        opts = parser.parse_args(args)
        logging.basicConfig(level=getattr(logging, opts.loglevel))
        with open(opts.config, 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

        return config, opts

    @classmethod
    def run_cli(cls):
        parser = cls.make_parser()
        config, opts = cls.use_parser(parser)
        config, opts = cls.inject_config_parameters(config, opts)
        task = cls.from_config(config)
        task(opts.dry)

    @classmethod
    def from_config(cls, cfg_dict):
        _logger.debug(f"Building {cls} from config")
        config = cfg_dict['config']
        inbox_cfg = config['inbox']
        boxtype = BOXTYPE_DISPATCH[inbox_cfg['type']]
        inbox = boxtype.from_config(inbox_cfg)
        bot = Bot.from_config(config['bot'])
        team = [
            TeamMember.from_config(member)
            for member in config['team']
        ]
        config = cfg_dict['workflows'].get(cls.CONFIG)
        return cls(inbox, bot, team, config)

    def _build_config(self):
        """
        Convert the values of the config dict to usable Python objects.

        This takes the configuration values of the YAML config file, stored
        as basic Python types in ``self.config``, and returns a dictionary
        that is more straightforwar to use in `:method:._run`.
        """
        raise NotImplementedError()

    def _run(self, config, dry):
        raise NotImplementedError()

    def __call__(self, dry=False):
        # skip early if not in config or not active
        if not self.config or not self.config.get("active", True):
            _logger.info(f"EXITING: Config for '{self.config}' not active")
            return

        # calling param takes precedence (testing), then
        dry = dry or self.config.get('dry', False)

        cfg_dict = {k: v for k, v in self.config.items()
                    if k not in {"active", "dry"}}
        cfg = self._build_config()
        _logger.info(f"Running {self} with config {cfg}")
        self._run(cfg, dry)
