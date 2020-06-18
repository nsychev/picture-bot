#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import emoji
import functools
import logging
import math
import threading
from queue import Queue
from telegram import Bot
from telegram.ext import Updater, Dispatcher, CallbackQueryHandler, CommandHandler, MessageHandler
from telegram.ext.filters import Filters

import actions
import config
import routes
import trash
from models import database, User, Post, Vote

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def initialize_webhook():
    bot = Bot(config.TOKEN)
    update_queue = Queue()
    dp = Dispatcher(bot, update_queue)

    threading.Thread(target=dp.start, name='dispatcher').start()

    return bot, dp, update_queue


def add_actions(dp):
    dp.add_handler(CommandHandler('start', actions.start))
    dp.add_handler(CommandHandler('rating', actions.social_rating))
    dp.add_handler(CallbackQueryHandler(actions.confirm_action, pattern='^confirm'))
    dp.add_handler(CallbackQueryHandler(actions.decline_action, pattern='^decline'))
    dp.add_handler(CallbackQueryHandler(actions.vote_action, pattern='^(like|hate)'))
    dp.add_handler(MessageHandler(Filters.photo, actions.picture))
    dp.add_handler(MessageHandler(Filters.all, actions.echo))
    dp.add_error_handler(actions.error)


def create_app():
    database.connect()

    if config.WEBHOOK:
        bot, dispatcher, update_queue = initialize_webhook()
        bot.set_webhook(f"https://pictures.nsychev.ru/{config.PATH}")
    else:
        updater = Updater(config.TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        bot = updater.bot
        update_queue = None

        bot.delete_webhook()
    
    add_actions(dispatcher)
    app = routes.create_app(bot, update_queue)

    if not config.WEBHOOK:
        def poll():
            updater.start_polling()
            updater.idle()
        
        threading.Thread(target=poll, name='poller').start()

    return app
