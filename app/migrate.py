#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from models import database, User, Post, Vote

database.connect()
database.create_tables([User, Post, Vote])