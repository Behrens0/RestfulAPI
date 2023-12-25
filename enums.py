from enum import Enum

class StatusEnum(str, Enum):
    Active = 'A'
    Inactive = 'I'
    Trash = 'trash'