#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import utils
from models import database, User, Post, Vote

database.connect()

old_v = User.get(User.id == 1001112599)
new_v = User.get(User.id == 1164432500)

for post in Post.select().where(Post.user == old_v):
    post.user = new_v
    post.save()

for vote in Vote.select().where(Vote.user == old_v):
    vote.user = new_v
    vote.save()

User.update({User.rating: 0}).execute()
Post.update({Post.rating: 0}).execute()

for vote in Vote.select().order_by(Vote.id.asc()):
    delta = utils.get_delta(vote.user.rating)
    if vote.delta < -vote.delta:
        delta *= -1

    vote.post.rating += delta
    vote.post.save()
    vote.post.user.rating += delta
    vote.post.user.save()
    vote.delta = delta
    vote.save()
