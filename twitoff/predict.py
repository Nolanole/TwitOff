import numpy as np
import pickle
from sklearn.linear_model import LogisticRegression
from .models import DB, User, Tweet, Comparison
from .twitter import BASILICA


def predict_user(user1_name, user2_name, tweet_text, cache=None):
  '''Determine and return which user is more likely to say a given tweet'''
  #user_set = pickle.dumps((user1_name, user2_name)) #users are sorted
  if cache and cache.exists(user_set):
    log_reg = pickle.loads(cache.get(user_set))
  else:
    user1 = User.query.filter(User.name == user1_name).one()
    user2 = User.query.filter(User.name == user2_name).one()
    user1_embeddings = np.array([tweet.embedding for tweet in user1.tweets])
    user2_embeddings = np.array([tweet.embedding for tweet in user2.tweets])
    embeddings = np.vstack([user1_embeddings, user2_embeddings])
    labels = np.concatenate([np.ones(len(user1.tweets)),
                             np.zeros(len(user2.tweets))])
    log_reg = LogisticRegression().fit(embeddings, labels)
    #cache and cache.set(user_set, pickle.dumps(log_reg))
  tweet_embedding = BASILICA.embed_sentence(tweet_text, model='twitter')
  prediction = int(log_reg.predict(np.array(tweet_embedding).reshape(1, -1))[0])
  probabilities = log_reg.predict_proba(np.array(tweet_embedding).reshape(1, -1))[0]
  predicted_user = user1_name if prediction == 1 else user2_name
  
  db_comparison = Comparison(text=tweet_text, predicted_user=predicted_user, 
                             user1_name=user1_name, user2_name=user2_name, 
                             user1_prob=probabilities[1], user2_prob=probabilities[0])
  DB.session.add(db_comparison)
  DB.session.commit()
  
  return tweet_text, predicted_user, user1_name, str(round(probabilities[1]*100,2))+'%', user2_name, str(round(probabilities[0]*100, 2))+'%'
  
  
  

'''
from twitoff.twitter import *
from twitoff.predict import *
u1 = 'Austen'
u2 = 'elonmusk'
tweet = 'Hey guys- Tesla and SpaceX are great!'
predict_user(u1, u2, tweet)
'''