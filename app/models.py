import datetime
from peewee import SqliteDatabase, IntegerField, CharField, BooleanField, AutoField, DateTimeField, ForeignKeyField, Model, FloatField


database = SqliteDatabase("pics.db")


class User(Model):
    id = IntegerField(primary_key=True)
    first_name = CharField(max_length=100)
    last_name = CharField(max_length=100)
    username = CharField(max_length=100)

    rating = FloatField(default=1)
    banned = BooleanField(default=False, null=True)

    created = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = database


class Post(Model):
    id = IntegerField(primary_key=True)
    user = ForeignKeyField(User, related_name='posts')
    
    likes = IntegerField(default=0)
    dislikes = IntegerField(default=0)
    rating = FloatField(default=0)

    buttons = CharField(max_length=16)

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