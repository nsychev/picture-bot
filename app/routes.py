import flask
from queue import Queue
from telegram import Bot, Update

import config


def create_app(bot: Bot, update_queue: Queue) -> flask.Flask:
    # pylint: disable=unused-variable

    app = flask.Flask(__name__)

    @app.route(f'/{config.PATH}', methods=['POST'])
    def webhook():
        update = Update.de_json(flask.request.json(), bot)
        update_queue.put(update)
        return ""

    return app
