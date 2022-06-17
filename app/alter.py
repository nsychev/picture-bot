#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from models import database, User, Post, Vote
from playhouse.migrate import *

database.connect()
migrator = SqliteMigrator(database)
migrate(
    migrator.add_column('post', 'created', Post.created),
    migrator.add_column('vote', 'created', Vote.created)
)
