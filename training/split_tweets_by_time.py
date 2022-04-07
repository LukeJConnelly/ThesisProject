import json
from datetime import datetime

found_tweets = json.load(open('../found/found_tweets.json'))
dates = []
for user in found_tweets:
    tweet_list = found_tweets[user]
    for tweet in tweet_list:
        dates.append(datetime.strptime(tweet["datetime"], "%Y-%m-%d %H:%M:%S"))

cutoff = sorted(dates)[int(len(dates) * 0.7)]
is_training = [d < cutoff for d in dates]
print(str(is_training).lower())
print("Split Train:Test =", sum(is_training), ":", len(is_training)-sum(is_training))
