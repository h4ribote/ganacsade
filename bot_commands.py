from discord import app_commands, Embed, Color, User, File
from time import time as _f_time

def time() -> int:
    return int(_f_time)

def setup(tree: app_commands.CommandTree):
    ...
