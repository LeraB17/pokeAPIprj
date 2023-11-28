from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from settings import *
from settings import db
from flask_login import UserMixin

class Fight(db.Model):
    __tablename__ = 'fights'
    id = db.Column(db.Integer, primary_key=True)
    select_pokemon = db.Column(db.String(150), nullable=False)
    vs_pokemon = db.Column(db.String(150), nullable=False)
    win = db.Column(db.Boolean, nullable=False)
    date_time = db.Column(db.DateTime(timezone=True), nullable=False, default=db.func.current_timestamp())
    rounds = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='cascade'), nullable=True)
    user = db.relationship('User', backref=db.backref('fights', lazy=True), cascade='all, delete')
    
    def __repr__(self):
	    return "<{}:{} vs {}>".format(self.id, self.select_pokemon, self.vs_pokemon)
        
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(100), nullable=False)
    created_on = db.Column(db.DateTime(), default=db.func.current_timestamp())
    updated_on = db.Column(db.DateTime(), default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
 
    def __init__(self, name, email, password_hash):
        self.name = name
        self.email = email
        self.set_password(password_hash)

    def __repr__(self):
	    return "<{}:{}:{}:{}>".format(self.id, self.name, self.email, self.password_hash)
