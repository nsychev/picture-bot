#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
from models import database, User, Post, Vote

database.connect()

users = {}

ctime = datetime.datetime(2020, 5, 1, 1, 1, 1)
mindiff = datetime.timedelta(hours=1)
for vote in Vote.select().where(Vote.id >= 2156 and Vote.id <= 2366):
    if vote.id >= 2156 and vote.id <= 2366:
        d = vote.created - ctime
        if d < datetime.timedelta(seconds=2):
            mindiff = d
            print(d)
        ctime = vote.created
    # print(vote.user.username)
    # k = f"{vote.post.user.username} {vote.delta > 0}"
    # users[k] = users.get(k, 0) + 1
print(mindiff)
print(users)
