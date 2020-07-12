# Imports
# ----------------------------------------------------------------------------#

import json
import os
import sys

import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from sqlalchemy import ARRAY, String
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

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

    def __repr__(self):
        return f'id: {self.id}, name: {self.name}'


class City(db.Model):
    __tablename__ = 'City'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey('State.id'), nullable=False)

    def __repr__(self):
        return f'id: {self.id}, name: {self.name}'

    def get_state(self):
        state = State.query.get(self.state_id)
        return state

    def get_venues(self):
        city_venues = Venue.query.filter_by(city=self.id).all()

        return {
            "city": self.name,
            "state": self.get_state().name,
            "venues": [
                venue.serialize() for venue in city_venues
            ]
        }

    def __repr__(self):
        state = State.query.get(self.state_id)
        if not state:
            result = f'id: {self.id}, name: {self.name}, state: None'
        else:
            result = f'id: {self.id}, name: {self.name}, state: {state.name}'
        return result


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime(), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    venue = db.relationship('Venue', backref='venue_shows', lazy=True)
    artist = db.relationship('Artist', backref='artist_shows', lazy=True)

    def __repr__(self):
        return f'id: {self.id}, venue: {self.venue.name}, artist: {self.artist.name}, on: {self.start_time}'

    def valid_time(self):
        artist = Artist.query.get(self.artist_id)
        time_hour = int(self.start_time.split(' ')[1][:2])
        return artist.available_from <= time_hour <= artist.available_till

    def serialize(self):
        return {
            "artist_id": self.artist.id,
            "artist_name": self.artist.name,
            "artist_image_link": self.artist.image_link,
            "start_time": self.start_time
        }

    def serialize_details(self):
        return {
            "venue_id": self.venue_id,
            "venue_name": self.venue.name,
            "artist_id": self.artist_id,
            "artist_name": self.artist.name,
            "artist_image_link": self.artist.image_link,
            "start_time": self.start_time
        }


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=False)
    genres = db.Column(db.String(), nullable=False, default='')
    city = db.Column(db.Integer, db.ForeignKey('City.id'), nullable=False)
    address = db.Column(db.String(120), nullable=False, default='')
    phone = db.Column(db.String(120), nullable=False, default='')
    website = db.Column(db.String(255), nullable=False, default='')
    facebook_link = db.Column(db.String(120), nullable=False, default='')
    seeking_talent = db.Column(db.Boolean(), nullable=False, default=False)
    seeking_description = db.Column(db.String(), nullable=True, default='')
    image_link = db.Column(db.String(500), nullable=False, default='')

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    def num_upcoming_shows(self):
        result = Show.query.filter(Show.venue_id == self.id).filter(Show.start_time >= datetime.now()).count()
        return result

    def __repr__(self):
        return f'id: {self.id}, name: {self.name}'

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "num_upcoming_shows": self.num_upcoming_shows(),
        }

    def serialize_details(self):
        city = City.query.get(self.city)
        past_shows = Show.query.filter(Show.start_time < datetime.now(),
                                       Show.venue_id == self.id).all()
        upcoming_shows = Show.query.filter(Show.start_time >= datetime.now(),
                                           Show.venue_id == self.id).all()
        past_shows_count = Show.query.filter(Show.start_time < datetime.now(),
                                             Show.venue_id == self.id).count()
        upcoming_shows_count = Show.query.filter(Show.start_time >= datetime.now(),
                                                 Show.venue_id == self.id).count()

        return {
            "id": self.id,
            "name": self.name,
            "genres": self.genres,
            "address": self.address,
            "city": city.name,
            "state": city.get_state().name,
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
    city = db.Column(db.Integer, db.ForeignKey('City.id'), nullable=False)
    phone = db.Column(db.String(120), nullable=False, default='')
    website = db.Column(db.String(255), nullable=False, default='')
    seeking_venue = db.Column(db.Boolean(), nullable=False, default=False)
    seeking_description = db.Column(db.String(), nullable=True, default='')
    genres = db.Column(db.String(), nullable=False, default='')
    image_link = db.Column(db.String(500), nullable=False, default='')
    facebook_link = db.Column(db.String(120), nullable=False, default='')
    available_from = db.Column(db.Integer(), nullable=True, default=0)
    available_till = db.Column(db.Integer(), nullable=True, default=23)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    def __repr__(self):
        return f'id: {self.id}, name: {self.name}'

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
        }

    def serialize_details(self):
        city = City.query.get(self.city)
        past_shows = Show.query.filter(Show.start_time < datetime.now(),
                                       Show.artist_id == self.id).all()
        upcoming_shows = Show.query.filter(Show.start_time >= datetime.now(),
                                           Show.artist_id == self.id).all()
        past_shows_count = Show.query.filter(Show.start_time < datetime.now(),
                                             Show.artist_id == self.id).count()
        upcoming_shows_count = Show.query.filter(Show.start_time >= datetime.now(),
                                                 Show.artist_id == self.id).count()
        return {
            "id": self.id,
            "name": self.name,
            "genres": self.genres,
            "city": city.name,
            "state": city.get_state().name,
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

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    print(value)
    date = dateutil.parser.parse(value)
    print(date)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# check if the city exists, if not it creates it
def validate_city(city_name, state_name):
    city = City.query.filter_by(name=city_name).first()
    if not city:
        state = State.query.filter_by(name=state_name).first()
        if not state:
            state = State(name=state_name)
            db.session.add(state)
            db.session.commit()
        city = City(name=city_name, state_id=state.id)
        db.session.add(city)
        db.session.commit()
    return city


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    last_added_artists = Artist.query.order_by(Artist.id.desc()).limit(10)
    last_added_venues = Venue.query.order_by(Venue.id.desc()).limit(10)
    return render_template('pages/home.html',
                           artists=last_added_artists,
                           venues=last_added_venues)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    cities = City.query.all()
    data = [city.get_venues() for city in cities]

    return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

    # query to search for a venue either by name, city, or state
    search_input = request.form['search_term']
    venues_found = db.session.query(Venue).join(City, State).filter(
        or_(
            Venue.name.ilike(f'%{search_input}%'),
            City.name.ilike(f'%{search_input}%'),
            State.name.ilike(f'%{search_input}%')
        )).all()
    venues_list = []
    for venue in venues_found:
        venues_list.append(venue.serialize())
    response = {
        "count": len(venues_list),
        "data": venues_list
    }

    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)
    data = venue.serialize_details()
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    try:
        # get city id if exists, or create it if it doesn't exist
        city = validate_city(request.form['city'], request.form['state'])

        # create new venue
        new_venue = Venue(
            name=request.form['name'],
            genres=request.form.getlist('genres'),
            city=city.id,
            address=request.form['address'],
            phone=request.form['phone'],
            website='',
            facebook_link=request.form['facebook_link'],
            seeking_talent=False,
            seeking_description='',
            image_link=''
        )

        db.session.add(new_venue)
        db.session.commit()

        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')

    except:
        # TODO: on unsuccessful db insert, flash an error instead.
        db.session.rollback()
        flash(sys.exc_info())
        abort(400)
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE', 'GET'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    succeeded = True
    try:
        venue = Venue.query.filter_by(id=venue_id)
        venue.delete()
        db.session.commit()
    except:
        succeeded = False
        db.session.rollback()
        flash(sys.exc_info())
    finally:
        db.session.close()

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage

    # js redirects to home page in case if succeeded
    return jsonify({'success': succeeded})


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    all_artists = Artist.query.all()
    data = [
        artist.serialize() for artist in all_artists
    ]

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".

    # query to search for a venue either by name, city, or state
    search_input = request.form['search_term']
    artists_found = db.session.query(Artist).join(City, State).filter(
        or_(
            Artist.name.ilike(f'%{search_input}%'),
            City.name.ilike(f'%{search_input}%'),
            State.name.ilike(f'%{search_input}%')
        )).all()
    artists_list = []
    for artist in artists_found:
        artists_list.append(artist.serialize())
    response = {
        "count": len(artists_list),
        "data": artists_found
    }

    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    artist = Artist.query.get(artist_id)
    data = artist.serialize_details()
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()

    # TODO: populate form with fields from artist with ID <artist_id>
    artist = Artist.query.get(artist_id)
    form.name.data = artist.name
    form.genres.data = artist.genres
    form.phone.data = artist.phone
    city = City.query.get(artist.city)
    form.city.data = city.name
    form.state.data = city.get_state()
    form.image_link.data = artist.image_link
    form.facebook_link.data = artist.facebook_link
    form.available_from.data = artist.available_from
    form.available_till.data = artist.available_till

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    artist = Artist.query.get(artist_id)

    artist.name = request.form['name']
    city = validate_city(request.form['city'], request.form['state'])
    artist.city = city.id
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.facebook_link = request.form['facebook_link']
    artist.available_from = request.form['available_from']
    artist.available_till = request.form['available_till']

    db.session.commit()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    # TODO: populate form with values from venue with ID <venue_id>
    venue = Venue.query.get(venue_id)
    form.name.data = venue.name
    form.genres.data = venue.genres
    form.phone.data = venue.phone
    city = City.query.get(venue.city)
    form.city.data = city.name
    form.state.data = city.get_state()
    form.image_link.data = venue.image_link
    form.facebook_link.data = venue.facebook_link
    form.address.data = venue.address

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.get(venue_id)
    venue.name = request.form['name']
    city = validate_city(request.form['city'], request.form['state'])
    venue.city = city.id
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.facebook_link = request.form['facebook_link']

    db.session.commit()

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    try:
        city = validate_city(request.form['city'], request.form['state'])

        # create new artist
        new_artist = Artist(
            name=request.form['name'],
            city=city.id,
            phone=request.form['phone'],
            genres=request.form.getlist('genres'),
            facebook_link=request.form['facebook_link'],
            available_from=request.form['available_from'],
            available_till=request.form['available_till']
        )
        db.session.add(new_artist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
        db.session.rollback()
        flash(sys.exc_info())
        abort(400)
    finally:
        db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    all_shows = Show.query.all()
    data = [
        show.serialize_details() for show in all_shows
    ]

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    new_show = Show(
        start_time=request.form['start_time'],
        artist_id=request.form['artist_id'],
        venue_id=request.form['venue_id']
    )

    if not new_show.valid_time():
        flash('Sorry, the artist is not available on this time!')
        return redirect(url_for('create_shows'))
    else:
        try:
            db.session.add(new_show)
            db.session.commit()
            # on successful db insert, flash success
            flash('Show was successfully listed!')
        except:
            # TODO: on unsuccessful db insert, flash an error instead.
            # e.g., flash('An error occurred. Show could not be listed.')
            # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
            db.session.rollback()
            flash(sys.exc_info())
            return redirect(url_for('create_shows'))
        finally:
            db.session.close()

        return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
