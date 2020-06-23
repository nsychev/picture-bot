from peewee import fn, JOIN
from models import database, User, Post, Vote

from io import BytesIO

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.dates import date2num, DateFormatter, DayLocator

from itertools import groupby
from functools import reduce
from datetime import datetime


def ratings():
    fig = Figure(figsize=(8,6))
    ax = fig.add_subplot(1, 1, 1)
    
    ax.set_prop_cycle(color=[
        '#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c', '#98df8a',
        '#d62728', '#ff9896', '#9467bd', '#c5b0d5', '#8c564b', '#c49c94',
        '#e377c2', '#f7b6d2', '#7f7f7f', '#c7c7c7', '#bcbd22', '#dbdb8d',
        '#17becf', '#9edae5'])
    
    votes_query = (Vote.select()
        .join(Post).join(User)
        .order_by(Vote.post.user))
    
    for key, group in groupby(votes_query, lambda x: x.post.user.username):
        votes = sorted(list(group), key=lambda x: x.created)
        times = [date2num(x.created) for x in votes]        
        times[-1] = date2num(datetime.now()) # stretch/align lines
        
        # oh the ugly mess
        deltas = [x.delta for x in votes][::-1]
        rating = votes[0].post.user.rating
        ratings = []
        for delta in deltas:
            rating -= delta
            ratings.append(rating)
        ratings = ratings[::-1]
            
        ax.plot_date(times, ratings, fmt="-", label=key)

    # sane dates
    ax.xaxis.set_major_formatter(DateFormatter("%F"))
    ax.xaxis.set_major_locator(DayLocator())
    ax.xaxis.set_tick_params(rotation=32)

    # styling
    ax.legend(loc='lower left', bbox_to_anchor= (0.0, 1.01),
              ncol=4, borderaxespad=0, frameon=False)
    ax.set(xlabel="əşəlme", ylabel="bəşəlme")        
    ax.grid(axis='both', color='0.95')
        
    fig.tight_layout()
    return fig


def to_bytes(plot):
    out = BytesIO()
    FigureCanvasAgg(plot).print_png(out)
    return out
