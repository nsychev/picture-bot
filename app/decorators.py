import functools
import os
from telegram import Update
from telegram.ext import CallbackContext
from typing import Callable

from models import User

TelegramAction = Callable[[Update, CallbackContext], None]


def attach_user(func: TelegramAction) -> TelegramAction:
    @functools.wraps(func)
    def wrapper(update: Update, context: CallbackContext):
        if update.message and update.message.chat.id < 0:
            return
        
        if update.message:
            user = update.message.from_user
        elif update.callback_query:
            user = update.callback_query.from_user
        else:
            return

        force_insert = False
        try:
            context.user = User.get(User.id == user.id)
        except:
            context.user = User()
            force_insert = True

        try:
            avatar = context.bot.get_user_profile_photos(user.id, offset=0, limit=1)
            avatar = avatar.photos[0][0]
            if context.user.avatar_id != avatar.file_unique_id:
                context.user.avatar_id = avatar.file_unique_id
                avatar.get_file().download(
                    os.path.join(
                        os.path.dirname(os.path.realpath(__file__)),
                        'static', f'{user.id}.jpg'
                    )
                )                
        except IndexError:
            context.user.avatar_id = None
            
        context.user.id = user.id
        context.user.first_name = user.first_name or ""
        context.user.last_name = user.last_name or ""
        context.user.username = user.username or "???"
        context.user.save(force_insert=force_insert)
        
        return func(update, context)
    
    return wrapper
