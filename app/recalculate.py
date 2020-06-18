#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import utils
from models import database, User, Post, Vote

database.connect()

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
