import datetime
from peewee import SqliteDatabase, IntegerField, CharField, BooleanField, AutoField, DateTimeField, ForeignKeyField, Model, FloatField
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

import utils

database = SqliteDatabase("pics.db")


class User(Model):
    id = IntegerField(primary_key=True)
    first_name = CharField(max_length=100)
    last_name = CharField(max_length=100)
    username = CharField(max_length=100)

    avatar_uid = CharField(max_length=128)

    rating = FloatField(default=0)
    banned = BooleanField(default=False, null=True)

    created = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = database


class Post(Model):
    id = AutoField(primary_key=True)
    user = ForeignKeyField(User, related_name='posts')
    
    likes = IntegerField(default=0)
    dislikes = IntegerField(default=0)
    rating = FloatField(default=0)

    buttons = CharField(max_length=16)

    message_id = IntegerField(unique=True, null=True)

    def emojis(self, idx):
        # pylint: disable=no-member
        return self.buttons.split('|')[idx]

    def get_arguments(self):
        return {
            "caption": utils.format_who(self.user),
            "parse_mode": "HTML",
            "reply_markup": InlineKeyboardMarkup([[
                InlineKeyboardButton(text=f'{self.emojis(0)} {self.likes or ""}', callback_data=f'like-{self.id}'),
                InlineKeyboardButton(text=f'{self.emojis(1)} {self.dislikes or ""}', callback_data=f'hate-{self.id}')
            ]])
        }

    class Meta:
        database = database


class Vote(Model):
    id = AutoField(primary_key=True)

    user = ForeignKeyField(User, related_name='reactions')
    post = ForeignKeyField(Post, related_name='reactions')

    positive = BooleanField()

    delta = FloatField()

    class Meta:
        database = database
        indexes = ((('user', 'post'), True), )
