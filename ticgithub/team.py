from dataclasses import dataclass

@dataclass
class TeamMember:
    github: str
    email: str
    label: str  # label is gmail-specific

    @classmethod
    def from_config(cls, config):
        return cls(**config)
