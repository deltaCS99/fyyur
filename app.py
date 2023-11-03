#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import os
import sys
import dateutil.parser
import babel
from flask import Flask, abort, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
print('CONNECTED !')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

#Venue Model
class Venue(db.Model):
    __tablename__ = "Venue"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String(120)), default=[])
    address = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    shows = db.relationship("Show", backref="venue", lazy=False, cascade="all, delete")

    def __repr__(self):
        return f'<Todo ID: {self.id}, description: {self.name }, complete: {self.genres}>'

#Artist Model
class Artist(db.Model):
    __tablename__ = "Artist"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String(120)), default=[])
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    shows = db.relationship("Show", backref="artist", lazy=False, cascade="all, delete")

#Show Model
class Show(db.Model):
    __tablename__ = "Show"

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey("Artist.id"), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey("Venue.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

#Changed the function to take strings also as it was only datetime objects and converting them to string
def format_datetime(value, format='medium'):
  if isinstance(value, str):
    date = dateutil.parser.parse(value)
  else: 
    date =value
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#
#home page route and controller
@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
#venues route and controller displays all venues
@app.route('/venues')
def venues():
  data = []  
  distinct_areas =  Venue.query.distinct(Venue.city, Venue.state).all()#a list of venues with distinct cities and states
  for area in distinct_areas:
    venue_areas = {
      'city':area.city,
      'state':area.state
    }
    venues_arr = []  
    venues = Venue.query.filter_by(city=area.city , state=area.state).all()
    for venue in venues:
      
      shows = Show.query.filter_by(venue_id=venue.id).all()#filtering all the shows with the particular venue id in order to calculate upcoming shows
      num_upcoming_shows = 0
      for show in shows:
        if show.start_time > datetime.now():
          num_upcoming_shows+=1
      venues_arr.append(
        {
          'id':venue.id,
          'name':venue.name,
          'num_upcoming_shows': num_upcoming_shows,
        }
      )
    venue_areas['venues'] = venues_arr
    data.append(venue_areas)
  return render_template('pages/venues.html', areas=data);

#route and controller for searching venues
@app.route('/venues/search', methods=['POST'])
def search_venues():
  response = {}
  search_term=request.form.get('search_term', '')
  venues_like = Venue.query.filter(Venue.name.like(f"%{search_term}%")).all()
  response['count']=len(venues_like)
  response['data']=[]
  for venue in venues_like:
    num_upcoming_shows = 0
    shows = Show.query.filter_by(venue_id=venue.id).all()
    for show in shows:
      if show.start_time > datetime.now():
        num_upcoming_shows+=1
    venue_dict ={
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows':num_upcoming_shows
    }

    response['data'].append(venue_dict)

  return render_template('pages/search_venues.html', results=response, search_term=search_term)

#shows particular venue when given id
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  past_shows = []
  upcoming_shows = []
  past_shows_count = 0
  upcoming_shows_count = 0
  

  data = Venue.query.get(venue_id)

  shows = Show.query.filter_by(venue_id=venue_id).all()
  for show in shows:
    """ Attempt to do join"""
    """ artist = db.session.query(show.artist.id, show.artist.name, Artist.image_link, Show.start_time).filter(Show.artist_id  == Artist.id ).filter(Artist.id ==show.artist_id).all()[0] """

    if show.start_time > datetime.now():
      upcoming_shows.append(
        {
        'artist_id':show.artist.id,
        'artist_name':show.artist.name,
        'artist_image_link':show.artist.image_link,
        'start_time':show.start_time
      }
      )
      upcoming_shows_count += 1
    else :
      past_shows.append({
        'artist_id':show.artist.id,
        'artist_name':show.artist.name,
        'artist_image_link':show.artist.image_link,
        'start_time':show.start_time
      }
      )
      past_shows_count += 1

  setattr(data, "past_shows", past_shows)
  setattr(data, "upcoming_shows", upcoming_shows) 
  setattr(data, "past_shows_count", past_shows_count) 
  setattr(data, "upcoming_shows_count", upcoming_shows_count)

  return render_template('pages/show_venue.html', venue=data)
  

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

#retrieves input from form and creates venue object upon succesful validation
@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form)
  if form.validate():
    venue = Venue(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        address = form.address.data,
        phone = form.phone.data,
        image_link = form.image_link.data,
        genres = form.genres.data,
        facebook_link = form.facebook_link.data,
        website = form.website_link.data,
        seeking_talent = form.seeking_talent.data,
        seeking_description = form.seeking_description.data
      )

    try:
      db.session.add(venue)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was listed!')
    except:
      db.session.rollback()
      print(sys.exc_info())
      flash('Venue ' + request.form['name'] + ' wasnt listed!')
      return redirect(url_for('index'))
    finally:
        db.session.close()
  return redirect(url_for('index'))

@app.route('/venues/<venue_id>/delete', methods=['GET'])
def delete_venue(venue_id):
  if request.method == 'GET':
    try:
      venue = Venue.query.get(venue_id)
      db.session.delete(venue)
      db.session.commit()
      flash('Venue deleted !')   
    except:
      db.session.rollback()
      flash('Venue not deleted !')  
    finally:
        db.session.close()   
  return redirect(url_for('index'))
  

#  Artists
#  ----------------------------------------------------------------
#route to display all artists
@app.route('/artists')
def artists():
  data = []
  data = db.session.query(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=data)

#route to search for particular
@app.route('/artists/search', methods=['POST'])
def search_artists():
  response = {}
  search_term=request.form.get('search_term', '')
  artists_like = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()
  response['count']=len(artists_like)
  response['data']=[]

  for artist in artists_like:
    num_upcoming_shows = 0
    shows = Show.query.filter_by(artist_id=artist.id).all()

    for show in shows:
      if show.start_time > datetime.now():
        num_upcoming_shows+=1

    artist_dict ={
      'id': artist.id,
      'name': artist.name,
      'num_upcoming_shows':num_upcoming_shows
    }

    response['data'].append(artist_dict)
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

#show artist given particular id
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    past_shows = []
    upcoming_shows = []
    past_shows_count = 0
    upcoming_shows_count = 0
    

    data = Artist.query.get(artist_id)

    shows = Show.query.filter_by(artist_id=artist_id).all()
    for show in shows:
      """ Attempt to do join"""
      """ artist = db.session.query(show.artist.id, show.artist.name, Artist.image_link, Show.start_time).filter(Show.artist_id  == Artist.id ).filter(Artist.id ==show.artist_id).all()[0] """

      if show.start_time > datetime.now():
        upcoming_shows.append(
          {
          'venue_id':show.venue.id,
          'venue_name':show.venue.name,
          'venue_image_link':show.venue.image_link,
          'start_time':show.start_time
        }
        )
        upcoming_shows_count += 1
      else :
        past_shows.append({
          'venue_id':show.venue.id,
          'venue_name':show.venue.name,
          'venue_image_link':show.venue.image_link,
          'start_time':show.start_time
        }
        )
        past_shows_count += 1

    setattr(data, "past_shows", past_shows)
    setattr(data, "upcoming_shows", upcoming_shows) 
    setattr(data, "past_shows_count", past_shows_count) 
    setattr(data, "upcoming_shows_count", upcoming_shows_count)

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj = artist)
  return render_template('forms/edit_artist.html', form=form,artist=artist)

#route to edit artist submission given particular artist  id
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)
  if request.method == 'POST'and form.validate():
    try:
      artist = Artist.query.get(artist_id)

      artist.name = form.name.data
      artist.city = form.city.data
      artist.state = form.state.data
      artist.phone = form.phone.data
      artist.image_link = form.image_link.data
      artist.genres = form.genres.data
      artist.facebook_link = form.facebook_link.data
      artist.website_link = form.website_link.data
      artist.seeking_venue = form.seeking_venue.data
      artist.seeking_description = form.seeking_description.data
      
      db.session.add(artist)
      db.session.commit()
      flash('Artist Edited')
    except:
      flash('Didnt edit')
      db.session.rollback()
    finally:
        db.session.close()
  else:
    flash(form.errors)
    return render_template('pages/home.html')
  return redirect(url_for('show_artist', artist_id=artist_id))
  

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj = venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

#route to edit artist submission given particular artist  id
@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form)
  if form.validate():
    try:
      venue = Venue.query.get(venue_id)

      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.address = form.address.data
      venue.phone = form.phone.data
      venue.image_link = form.image_link.data
      venue.genres = form.genres.data
      venue.facebook_link = form.facebook_link.data
      venue.website_link = form.website_link.data
      venue.seeking_talent = form.seeking_talent.data
      venue.seeking_description = form.seeking_description.data
      
      db.session.add(venue)
      db.session.commit()
      flash('Venue Edited !')
    except:
      flash('Didnt edit')
      db.session.rollback()
    finally:
        db.session.close()
  else:
    flash(form.errors)
    return render_template('pages/home.html')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

#create new artist given form submission
@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form)
  if form.validate():
    artist = Artist(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        phone = form.phone.data,
        image_link = form.image_link.data,
        genres = form.genres.data,
        facebook_link = form.facebook_link.data,
        website = form.website_link.data,
        seeking_venue = form.seeking_venue.data,
        seeking_description = form.seeking_description.data
      )

    try:
      db.session.add(artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was listed!')
    except:
      db.session.rollback()
      print(sys.exc_info())
      flash('Artist ' + request.form['name'] + ' wasnt listed!')
      return redirect(url_for('index'))
    finally:
        db.session.close()
  return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

#display all shows
@app.route('/shows')
def shows():
  data = []
    
  allShows = Show.query.all()

  for show in allShows:
    data.append(
      {
        'venue_id' :show.venue.id,
        'venue_name' :show.venue.name,
        'artist_id' :show.artist.id,
        'artist_name' :show.artist.name,
        'artist_image_link' :show.artist.image_link,
        'start_time' :show.start_time,
      }
    )
  return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

#create a show given form submission
@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  form = ShowForm(request.form)
  if form.validate():

    
    show = Show(
        artist_id= form.artist_id.data,
        venue_id = form.venue_id.data,
        start_time = form.start_time.data
    )
    try:
      db.session.add(show)
      db.session.commit()
      flash('Show was successfully listed!')
    except:
      flash('Show wasnt successfully listed!')
      db.session.rollback()
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

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
""" if __name__ == '__main__':
    app.run()
 """
# Or specify port manually:

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)

