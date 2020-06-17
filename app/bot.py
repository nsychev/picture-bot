#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import emoji
import functools
import logging
import math
import telegram
import telegram.ext

from telegram.ext.filters import Filters

import config
import trash
from models import database, User, Post, Vote

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def attach_user(func):
    @functools.wraps(func)
    def wrapper(update, context):
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
        
        context.user.id = user.id
        context.user.first_name = user.first_name or ""
        context.user.last_name = user.last_name or ""
        context.user.username = user.username or ""
        context.user.save(force_insert=force_insert)
        
        return func(update, context)
    
    return wrapper



@attach_user
def start(update, context):
    if context.user.banned is None:
        update.message.reply_text(trash.REQUESTED)
        context.bot.send_message(
            chat_id=config.ADMIN_ID,
            text=trash.REQUEST.format(user=context.user),
            reply_markup=telegram.InlineKeyboardMarkup([
                [telegram.InlineKeyboardButton(
                    text="Одобрить заявление",
                    callback_data=f"confirm-{context.user.id}"
                )],
                [telegram.InlineKeyboardButton(
                    text="Отклонить заявление",
                    callback_data=f"decline-{context.user.id}"
                )]
            ]),
            parse_mode="HTML"
        )
        context.user.banned = True
        context.user.save()
    elif context.user.banned:
        update.message.reply_text(trash.BANNED)
    else:
        update.message.reply_text(trash.APPROVED)


def get_delta(rating):
    if rating <= 0:
        return math.tanh(rating) / 2 + 0.5
    else:
        return math.log(rating + 1) / 2 + 0.5


def format_who(user, html=True):
    if user.username:
        return f"@{user.username}"
    
    if html:
        return f'<a href="tg://user?id={user.id}">{user.first_name} {user.last_name}</a>'
    else:
        return f'[{user.id}] {user.first_name} {user.last_name}'


@attach_user
def echo(update, context):
    update.message.reply_text("faux! Interdit\n\nПри повторении попытки блокировки Вы можете быть ЗАБАНЕНЫ")
    logger.warning(f"{context.user.id} wrong!")


@attach_user
def confirm_action(update, context):
    if context.user.id != config.ADMIN_ID:
        return
    
    user_id = int(update.callback_query.data[8:])
    update.callback_query.answer(text="Вы подтвердили!", show_alert=True)
    update.callback_query.message.edit_text(f"Вы подтвердили {user_id}")

    user = User.get(User.id == user_id)
    user.banned = False
    user.save()

    context.bot.send_message(
        chat_id=user_id,
        text=trash.APPROVED
    )


@attach_user
def decline_action(update, context):
    if context.user.id != config.ADMIN_ID:
        return
    
    user_id = int(update.callback_query.data[8:])
    update.callback_query.answer(text="Вы отклонили!", show_alert=True)
    update.callback_query.message.edit_text(f"Вы отклонили {user_id}")

    context.bot.send_message(
        chat_id=user_id,
        text=trash.DECLINED
    )


@attach_user
def picture(update, context):
    best_photo = max(update.message.photo, key=lambda p: p.file_size)
    file_id = best_photo.file_id
    
    text = update.message.caption
    if text is not None:
        text = text.strip()
        if len(text.split()) == 2:
            emojis = text.split()
        elif len(text) == 2:
            emojis = list(text)
        else:
            emojis = [None, None]
        
        if emojis[0] not in emoji.UNICODE_EMOJI or emojis[1] not in emoji.UNICODE_EMOJI:
            update.message.reply_text("Ваш бюллютень НЕДЕЙСТВИТЕЛЕН. Используйте 2 (два) альтернативных эмодзи, разделённых символом (пробел). Иные символы wrong.")
    else:
        emojis = ["📈", "📉"]
    
    post = context.bot.send_photo(
        config.CHANNEL_ID,
        photo=file_id,
        caption=format_who(context.user),
        parse_mode="HTML",
        reply_markup=telegram.InlineKeyboardMarkup([[
            telegram.InlineKeyboardButton(text=emojis[0], callback_data='like'),
            telegram.InlineKeyboardButton(text=emojis[1], callback_data='dislike')
        ]])
    )

    Post.create(id=post.message_id, user=context.user, buttons='|'.join(emojis))

    update.message.reply_text('Администрация ИС Бот выражает Вам благодарность за пост!')


@attach_user
def vote_action(update, context):
    post = Post.get(Post.id == int(update.callback_query.data[5:]))

    if context.user == post.user:
        update.callback_query.answer(text="ЗАПРЕЩЕНО WRONG СЕЙЧАС ЖЕ ОСТАНОВИТЕСЬ!!!!", show_alert=True)
        logger.warn(f"{format_who(context.user, False)} selflike")
        return

    liked = update.callback_query.data.startswith("like")
    delta = get_delta(context.user.rating)

    if liked:
        post.likes += 1
    else:
        post.dislikes += 1
        delta *= -1
    
    post.rating += delta
    post.user.rating += delta
    
    try:
        Vote.create(
            user=context.user,
            post=post,
            positive=liked,
            delta=delta
        )
    except:
        update.callback_query.answer(text='Один голос РАЗРЕШЕНО \nмного голосов ЗАПРЕЩЕНО', show_alert=True)
        return
    
    post.save()
    post.user.save()

    context.bot.edit_message_caption(
        chat_id=config.CHANNEL_ID,
        message_id=post.id,
        caption=format_who(post.user),
        reply_markup=telegram.InlineKeyboardMarkup([[
            telegram.InlineKeyboardButton(
                text=f"{post.buttons.split('|')[0]} {post.likes or ''}", 
                callback_data=f'like-{post.id}'
            ),
            telegram.InlineKeyboardButton(
                text=f"{post.buttons.split('|')[1]} {post.dislikes or ''}", 
                callback_data=f'hate-{post.id}'
            )
        ]])
    )
    update.callback_query.answer(text="Голосование завершено!", show_alert=True)


def error(update, context):
    logger.error(msg="Exception happened", exc_info=context.error)
    if update.message:
        update.message.reply_text("faux! Interdit... administration des appels")
    elif update.callback_query:
        update.callback_query.message.reply_text("faux! Interdit... administration des appels")


def main():
    database.connect()

    updater = telegram.ext.Updater(config.TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(telegram.ext.CommandHandler('start', start))
    dp.add_handler(telegram.ext.CallbackQueryHandler(confirm_action, pattern='^confirm'))
    dp.add_handler(telegram.ext.CallbackQueryHandler(decline_action, pattern='^decline'))
    dp.add_handler(telegram.ext.CallbackQueryHandler(vote_action, pattern='^(like|hate)'))
    dp.add_handler(telegram.ext.MessageHandler(Filters.photo, picture))
    dp.add_handler(telegram.ext.MessageHandler(Filters.all, echo))
    dp.add_error_handler(error)

    if config.WEBHOOK:
        updater.start_webhook(listen="127.0.0.1", port=27062, url_path=config.PATH)
        updater.bot.set_webhook(f"https://pictures.nsychev.ru/{config.PATH}")
    else:
        updater.start_polling()
        updater.idle()


if __name__ == "__main__":
    main()