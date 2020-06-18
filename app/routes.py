import flask
from queue import Queue
from telegram import Bot, Update

import config
from models import database, User, Post


def create_app(bot: Bot, update_queue: Queue) -> flask.Flask:
    # pylint: disable=unused-variable

    app = flask.Flask(__name__)

    @app.route(f'/{config.PATH}', methods=['POST'])
    def webhook():
        update = Update.de_json(flask.request.json, bot)
        update_queue.put(update)
        return ""

    @app.route('/')
    def top():
        users_query = User.select().where(User.rating > 0).order_by(User.rating.desc())
        users = [{
            'id': user.id,
            'first': user.first_name or user.username,
            'last': user.last_name,
            'rating': round(user.rating, 5),
            'posts': Post.select().where(Post.user == user).count(),
            'position': idx + 1
        } for idx, user in enumerate(users_query)]        
        return flask.render_template('top.html', users=users)

    return app

