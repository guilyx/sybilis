from dataclasses import dataclass


@dataclass
class Account:
    address: str
    private_key: str

    @classmethod
    def from_dict(cls, account_dict):
        return cls(**account_dict)
