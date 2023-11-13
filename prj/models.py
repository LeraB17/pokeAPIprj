from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from settings import *

db = SQLAlchemy()

class Fight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    select_pokemon = db.Column(db.String(150), nullable=False)
    vs_pokemon = db.Column(db.String(150), nullable=False)
    win = db.Column(db.Boolean, nullable=False)
    date_time = db.Column(db.DateTime(timezone=True), nullable=False, default=db.func.current_timestamp())
    rounds = db.Column(db.Integer, nullable=False)
        
