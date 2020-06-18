import emoji
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

import config
import trash
import utils
from decorators import attach_user
from models import User, Post, Vote

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


@attach_user
def start(update: Update, context: CallbackContext):
    if context.user.banned is None:
        update.message.reply_text(trash.REQUESTED)
        context.bot.send_message(
            chat_id=config.ADMIN_ID,
            text=trash.REQUEST.format(user=context.user),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Одобрить заявление",
                    callback_data=f"confirm-{context.user.id}"
                )],
                [InlineKeyboardButton(
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


@attach_user
def echo(update: Update, context: CallbackContext):
    update.message.reply_text("faux! Interdit\n\nПри повторении попытки блокировки Вы можете быть ЗАБАНЕНЫ")
    logger.warning(f"{context.user.id} wrong!")


@attach_user
def confirm_action(update: Update, context: CallbackContext):
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
def decline_action(update: Update, context: CallbackContext):
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
def picture(update: Update, context: CallbackContext):
    try:
        post_time = Post.select().where(Post.user == context.user).order_by(Post.created.desc()).get().created
        timeout = utils.get_ban_time(context.user.rating)

        allow_at = post_time + timedelta(seconds=timeout)

        if allow_at > datetime.now():
            update.message.reply_text(f"Администрация ИС Бот в целях предотвращения спама в ИС Канал не даёт публиковать изображения до {allow_at}.")
            return
    except Post.DoesNotExist:
        pass


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
            return
    else:
        emojis = ["📈", "📉"]
    
    post = Post.create(user=context.user, buttons='|'.join(emojis))
    
    message = context.bot.send_photo(
        config.CHANNEL_ID,
        photo=file_id,
        **post.get_arguments()
    )

    post.message_id = message.message_id
    post.save()

    update.message.reply_text(trash.POSTED.format(post=post))


@attach_user
def vote_action(update: Update, context: CallbackContext):
    if not config.VOTING:
        update.callback_query.answer(text="ИЗВИНИТЕ! система находится на реконструкции")
    post = Post.get(Post.id == int(update.callback_query.data[5:]))

    if context.user == post.user:
        update.callback_query.answer(text="ЗАПРЕЩЕНО WRONG СЕЙЧАС ЖЕ ОСТАНОВИТЕСЬ!!!!", show_alert=True)
        logger.warning(f"{utils.format_who(context.user, False)} selflike")
        return

    liked = update.callback_query.data.startswith("like")
    delta = utils.get_delta(context.user.rating)

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
        message_id=post.message_id,
        **post.get_arguments()
    )
    update.callback_query.answer(text="Голосование совершено!", show_alert=True)


@attach_user
def social_rating(update: Update, context: CallbackContext):
    update.message.reply_text(f'Уважаемый пользователь! Ваш социальный рейтинг: **{context.user.rating}**. Постируйте хорошее и не постируйте плохое, чтобы его увеличить.', parse_mode="Markdown")


def error(update: Update, context: CallbackContext):
    logger.error(msg="Exception happened", exc_info=context.error)
    if update.message:
        if update.message.chat.id > 0:
            update.message.reply_text("faux! Interdit... administration des appels")
        else:
            context.bot.send_message(chat_id=config.ADMIN_ID, text=f"faux! faux! faux! {update.message.message_id}")
    elif update.callback_query:
        try:
            update.callback_query.message.reply_text("faux! Interdit... administration des appels")
        except:
            # don't retry
            pass
