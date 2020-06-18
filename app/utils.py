import math
from telegram import User


def get_delta(rating: float) -> float:
    if rating <= 0:
        return math.tanh(rating) / 2 + 0.5
    else:
        return math.log(rating + 1) / 2 + 0.5


def get_ban_time(rating: float) -> float:
    return math.floor(math.exp(-rating / 5) * 60)


def format_who(user: User, html: bool = True) -> str:
    if user.username:
        return f"@{user.username}"
    
    if html:
        return f'<a href="tg://user?id={user.id}">{user.first_name} {user.last_name}</a>'
    else:
        return f'[{user.id}] {user.first_name} {user.last_name}'