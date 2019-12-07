# General:
import tweepy           # To consume Twitter's API
import pandas as pd     # To handle data
import numpy as np      # For number computing
import pickle           # For pickling data

# For plotting and visualization:
from IPython.display import display
import matplotlib.pyplot as plt
import seaborn as sns
'exec(%matplotlib inline)'
import time
import datetime

# For sentiment analysis:
from textblob import TextBlob
import re

# We import our access keys:
from credentials import *    # This allows us to use the keys as variables

from flask import Flask, render_template, request

from run_analysis import twitter_setup, get_tweets_by_username, process_tweets, show_text, show_len, show_date, show_ID, show_source, show_likes, show_RT, obtain_sources, clean_tweet, analyze_polarity, analyze_subjectivity

app = Flask(__name__)

@app.route("/sentimentanalysis", methods=["GET", "POST"])
def individual_sentiment_analysis():
    if request.method == "POST":
        input_keywords = request.form["keywords"]
        SCREEN_NAME = request.form['username']
        KEYWORDS = input_keywords.split(',')

        tweets = get_tweets_by_username(screen_name=SCREEN_NAME)

        tweet_list = list(tweets.items())

        with open(f'tweets_by_{SCREEN_NAME}.p', 'wb') as f:
            pickle.dump(tweet_list, f)

        with open(f'tweets_by_{SCREEN_NAME}.p', 'rb') as f:
            tweet_list = pickle.load(f)

        useful_tweets = process_tweets(tweet_list, KEYWORDS)
        useful_tweets_text = show_text(useful_tweets)
        useful_tweets_len = show_len(useful_tweets)
        useful_tweets_date = show_date(useful_tweets)
        useful_tweets_ID = show_ID(useful_tweets)
        useful_tweets_source = show_source(useful_tweets)
        useful_tweets_likes = show_likes(useful_tweets)
        useful_tweets_RT = show_RT(useful_tweets)

        total_tweets = len(useful_tweets)

        # We create a pandas dataframe as follows:
        data = pd.DataFrame(data=useful_tweets_text, columns=['Tweets'])

        # We add relevant data:
        data['len']  = np.array(useful_tweets_len)
        data['ID']   = np.array(useful_tweets_ID)
        data['Date'] = np.array(useful_tweets_date)
        data['Source'] = np.array(useful_tweets_source)
        data['Likes']  = np.array(useful_tweets_likes)
        data['RTs']    = np.array(useful_tweets_RT)

        # We extract the mean of lenghts:
        mean = np.mean(data['len'])
        rounded_mean = float(str(round(mean, 2)))

        # We extract the tweet with more FAVs and more RTs:
        fav_max = np.max(data['Likes'])
        rt_max  = np.max(data['RTs'])

        fav = data[data.Likes == fav_max].index[0]
        rt  = data[data.RTs == rt_max].index[0]

        most_fav = data['Tweets'][fav]
        most_rt = data['Tweets'][rt]

        most_fav_characters = data['len'][fav]
        most_rt_characters = data['len'][rt]

        # We create a column with the result of the analysis:
        data['Pol'] = np.array([ analyze_polarity(tweet) for tweet in data['Tweets'] ])
        data['Sub'] = np.array([ analyze_subjectivity(tweet) for tweet in data['Tweets'] ])

        display_last_10_tweets = data.head(10)

        pos_tweets = [ tweet for index, tweet in enumerate(data['Tweets']) if data['Pol'][index] > 0]
        neu_tweets = [ tweet for index, tweet in enumerate(data['Tweets']) if data['Pol'][index] == 0]
        neg_tweets = [ tweet for index, tweet in enumerate(data['Tweets']) if data['Pol'][index] < 0]

        percent_pos_tweets = len(pos_tweets)*100/len(data['Tweets'])
        percent_neu_tweets = len(neu_tweets)*100/len(data['Tweets'])
        percent_neg_tweets = len(neg_tweets)*100/len(data['Tweets'])

        rounded_percent_pos_tweets = float(str(round(percent_pos_tweets, 2)))
        rounded_percent_neu_tweets = float(str(round(percent_neu_tweets, 2)))
        rounded_percent_neg_tweets = float(str(round(percent_neg_tweets, 2)))

        tlen = pd.Series(data=data['len'].values, index=data['Date'])
        tfav = pd.Series(data=data['Likes'].values, index=data['Date'])
        tret = pd.Series(data=data['RTs'].values, index=data['Date'])

        tlen.plot(figsize=(16,4), color='r')
        plt.savefig('static/images/TweetLenghtVisualization.png')

        tfav.plot(figsize=(16,4), label="Likes", legend=True)
        tret.plot(figsize=(16,4), label="Retweets", legend=True)
        plt.savefig('static/images/LikesvsRetweetsVisualization.png')

        if useful_tweets:
            return render_template(
                "results.html", KEYWORDS=KEYWORDS, SCREEN_NAME=SCREEN_NAME, total_tweets=total_tweets, rounded_mean=rounded_mean, most_fav=most_fav, most_rt=most_rt, fav_max=fav_max, rt_max=rt_max, most_fav_characters=most_fav_characters, most_rt_characters=most_rt_characters, display_last_10_tweets=display_last_10_tweets.to_html(), rounded_percent_pos_tweets=rounded_percent_pos_tweets, rounded_percent_neu_tweets=rounded_percent_neu_tweets, rounded_percent_neg_tweets=rounded_percent_neg_tweets, TweetLenghtVisualization='/static/images/TweetLenghtVisualization.png', LikesvsRetweetsVisualization='/static/images/LikesvsRetweetsVisualization.png'
            )
        else:
            return render_template("index.html", error=True)
    return render_template("index.html", error=None)

@app.route("/")
def home():
    return render_template("homepage.html")

if __name__ == "__main__":
    app.run(debug=True)