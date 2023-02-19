


def core_config(config_file_dict):
    config = config_file_dict['config']
    inbox_cfg = config['inbox']
    boxtype = BOXTYPE_DISPATCH[inbox_cfg['type']]
    inbox = boxtype.from_config(inbox_cfg)
    bot = Bot.from_config(config['bot'])
    team = [
        TeamMember.from_config(member)
        for member in config['team']
    ]
    return inbox, bot, team
