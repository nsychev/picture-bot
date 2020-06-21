import flask
from queue import Queue
from peewee import fn, JOIN
from telegram import Bot, Update

import config
from models import database, User, Post

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import random
from io import BytesIO

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
        users_query = (User.select(User, fn.COUNT(Post.id).alias('count'))
            .join(Post, JOIN.LEFT_OUTER)
            .group_by(User.id)
            .order_by(User.rating.desc()))
        
        users = [{
            'id': user.id,
            'first': user.first_name or user.username,
            'last': user.last_name,
            'rating': round(user.rating, 5),
            'posts': user.count,
            'position': idx + 1
        } for idx, user in enumerate(users_query) if user.count > 0]
        return flask.render_template('top.html', users=users)

    @app.route('/grafik')
    def plot():
            fig = Figure(figsize=(16, 10))
            axis = fig.add_subplot(1, 1, 1)

            for i in range(10):
                xs = range(100)
                ys = [random.randint(1, 50) for x in xs]
                axis.plot(xs, ys)

            axis.set(
                xlabel="эшельме",
                ylabel="бэшельме",
                title="Հայոց պատմության 10 դասարան" 
            )
            return respond_with_figure(fig)

    def respond_with_figure(figure):
            canvas = FigureCanvas(figure)
            output = BytesIO()
            canvas.print_png(output)
            response = flask.make_response(output.getvalue())
            response.mimetype = 'image/png'
            return response

    return app

