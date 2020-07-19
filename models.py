from datetime import datetime

from flask import Flask
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#


# TODO: connect to a local postgresql database
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class State(db.Model):
    __tablename__ = 'State'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    cities = db.relationship('City', backref='state', lazy=True)

    def __repr__(self):
        return f'<State {self.id}, Name: {self.name}>'


class City(db.Model):
    __tablename__ = 'City'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey('State.id'), nullable=False)

    def __repr__(self):
        return f'<City {self.id}, Name: {self.name}>'

    def get_venues(self):
        city_venues = Venue.query.filter_by(city_id=self.id).all()

        return {
            "city": self.name,
            "state": self.state.name,
            "venues": [
                venue.serialize() for venue in city_venues
            ]
        }


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Show {self.id}, Artist: {self.artist_id}, Venue: {self.venue_id}>'

    def valid_time(self):
        """ to check if the artist time accepts the show time """
        time_hour = int(self.start_time.split(' ')[1][:2])
        artist = Artist.query.get(self.artist_id)
        return artist.available_from <= time_hour <= artist.available_till

    def serialize(self):
        artist = Artist.query.get(self.artist_id)
        return {
            "artist_id": self.artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": self.start_time
        }

    def serialize_details(self):
        artist = Artist.query.get(self.artist_id)
        venue = Venue.query.get(self.venue_id)
        return {
            "venue_id": self.venue_id,
            "venue_name": venue.name,
            "artist_id": self.artist_id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": self.start_time
        }


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    genres = db.Column(db.ARRAY(db.String()), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('City.id'), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=True, default='')
    website = db.Column(db.String(255), nullable=True, default='')
    facebook_link = db.Column(db.String(120), nullable=False, default='')
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False, server_default="false")
    seeking_description = db.Column(db.String, nullable=True, default='')
    shows = db.relationship('Show', backref='Venue', lazy=True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    def __repr__(self):
        return f'<Venue {self.id}, Name: {self.name}>'

    def num_upcoming_shows(self):
        result = Show.query.filter(Show.venue_id == self.id).filter(Show.start_time >= datetime.now()).count()
        return result

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "num_upcoming_shows": self.num_upcoming_shows(),
        }

    def serialize_details(self):

        past_shows = Show.query.filter(Show.start_time < datetime.now(),
                                       Show.venue_id == self.id).all()
        upcoming_shows = Show.query.filter(Show.start_time >= datetime.now(),
                                           Show.venue_id == self.id).all()
        past_shows_count = Show.query.filter(Show.start_time < datetime.now(),
                                             Show.venue_id == self.id).count()
        upcoming_shows_count = Show.query.filter(Show.start_time >= datetime.now(),
                                                 Show.venue_id == self.id).count()
        city = City.query.get(self.city_id)
        return {
            "id": self.id,
            "name": self.name,
            "genres": self.genres,
            "address": self.address,
            "city": city.name,
            "state": city.state.name,
            "phone": self.phone,
            "website": self.website,
            "facebook_link": self.facebook_link,
            "seeking_talent": self.seeking_talent,
            "seeking_description": self.seeking_description,
            "image_link": self.image_link,
            "past_shows": [
                show.serialize() for show in past_shows
            ],
            "upcoming_shows": [
                show.serialize() for show in upcoming_shows
            ],
            "past_shows_count": past_shows_count,
            "upcoming_shows_count": upcoming_shows_count,
        }


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    genres = db.Column(db.ARRAY(db.String()), nullable=False, default='')
    city_id = db.Column(db.Integer, db.ForeignKey('City.id'), nullable=False)
    phone = db.Column(db.String(120), nullable=False, default='')
    image_link = db.Column(db.String(500), nullable=False, default='')
    website = db.Column(db.String(255), nullable=False, default='')
    facebook_link = db.Column(db.String(120), nullable=False, default='')
    seeking_venue = db.Column(db.Boolean(), nullable=False, default=False)
    seeking_description = db.Column(db.String(), nullable=True, default='')
    available_from = db.Column(db.Integer(), nullable=True, default=0)
    available_till = db.Column(db.Integer(), nullable=True, default=23)
    shows = db.relationship('Show', backref='artist', lazy=True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    def __repr__(self):
        return f'<Artist {self.id}, Name: {self.name}>'

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
        }

    def serialize_details(self):

        past_shows = Show.query.filter(Show.start_time < datetime.now(),
                                       Show.artist_id == self.id).all()
        upcoming_shows = Show.query.filter(Show.start_time >= datetime.now(),
                                           Show.artist_id == self.id).all()
        past_shows_count = Show.query.filter(Show.start_time < datetime.now(),
                                             Show.artist_id == self.id).count()
        upcoming_shows_count = Show.query.filter(Show.start_time >= datetime.now(),
                                                 Show.artist_id == self.id).count()
        city = City.query.get(self.city_id)
        return {
            "id": self.id,
            "name": self.name,
            "genres": self.genres,
            "city": city.name,
            "state": city.state.name,
            "phone": self.phone,
            "website": self.website,
            "facebook_link": self.facebook_link,
            "seeking_venue": self.seeking_venue,
            "seeking_description": self.seeking_description,
            "image_link": self.image_link,
            "available_from": self.available_from,
            "available_till": self.available_till,
            "past_shows": [
                show.serialize() for show in past_shows
            ],
            "upcoming_shows": [
                show.serialize() for show in upcoming_shows
            ],
            "past_shows_count": past_shows_count,
            "upcoming_shows_count": upcoming_shows_count,
        }


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
