#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from models import database, User, Post, Vote

database.connect()

for user in User.select():
    print("User", user.id, user.username, user.rating, user.banned)

for post in Post.select():
    print("Post", post.id, post.message_id, post.user.id, post.likes, post.dislikes, post.rating, post.buttons)

for vote in Vote.select():
    print("Vote", vote.id, vote.user.id, vote.post.id, vote.positive, vote.delta)