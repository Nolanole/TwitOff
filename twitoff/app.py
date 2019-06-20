"""Main application and routing logic for TwitOff"""
from decouple import config
from flask import Flask, render_template, request
from .models import DB, User, Tweet, Comparison
from .twitter import add_or_update_user, update_all_users
from .predict import predict_user

def create_app():
  """Create and configure an instance of the Flask application"""
  app = Flask(__name__)
  app.config['SQLALCHEMY_DATABASE_URI'] = config('DATABASE_URL')
  app.config['SQLALCHEMY_TRACK_NOTIFICATIONS'] = False
  app.config['ENV'] = config('ENV')
  DB.init_app(app)

  @app.route('/')
  def root():
    users = User.query.all()
    comparisons = Comparison.query.all()
    return render_template('base.html', title='Home', users=users, comparisons=comparisons)

  @app.route('/reset')
  def reset():
    DB.drop_all()
    DB.create_all()
    return render_template('base.html', title='DB Reset', users=[])

  @app.route('/update')
  def update():
    '''if config('ENV') == 'production':
      CACHE.flushall()
      CACHED_COMPARISONS.clear()'''
    users = User.query.all()  
    update_all_users(users)
    return render_template('base.html', users=User.query.all(), 
                           title='Cache cleared and all tweets updated!')  
  
  @app.route('/user', methods=['POST'])
  @app.route('/user/<name>', methods=['GET'])
  def user(name=None):
    message = ''
    name = name or request.values['user_name']
    try:
      if request.method == 'POST':
        add_or_update_user(name)
        message = 'User {} successfully added!'.format(name)
      tweets = User.query.filter(User.name == name).one().tweets
    except Exception as e:
      message = 'Error adding {}: {}'.format(name, e)
      tweets = []
    return render_template('user.html', title=name, tweets=tweets, message=message)

  @app.route('/compare', methods=['POST'])
  def compare():
    user1 = request.values['user1']
    user2 = request.values['user2']
    tweet_text = request.values['tweet_text']
    tweet_text, predicted_user, user1_name, user1_prob, user2_name, user2_prob = predict_user(user1, user2, tweet_text)
    return render_template('compare.html', title='Twitoff prediction for which user is more likely to tweet: ', tweet=tweet_text,
                           predicted_user=predicted_user, user1_name=user1_name, user1_prob=user1_prob,
                           user2_name=user2_name, user2_prob=user2_prob)
  
  
  return app