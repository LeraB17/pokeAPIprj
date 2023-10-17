from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from db import db_connection_params
from datetime import datetime

connect_string = f'postgresql://{db_connection_params["username"]}:{db_connection_params["password"]}@localhost:5432/{db_connection_params["db_name"]}'

db = SQLAlchemy()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = connect_string
db.init_app(app)


class Fight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    select_pokemon = db.Column(db.String(150), nullable=False)
    vs_pokemon = db.Column(db.String(150), nullable=False)
    win = db.Column(db.Boolean, nullable=False)
    date_time = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.now())
    rounds = db.Column(db.Integer, nullable=False)


if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
        
