import tweepy
import json
import datetime
from classes.tweet import Tweet

env_file = open("env.json", 'r')
env_vars = json.load(env_file)

# Consumer keys and access tokens, used for OAuth
consumer_key = env_vars["twitter_consumer_key"]
consumer_secret = env_vars["twitter_consumer_secret"]
access_token = env_vars["twitter_access_token"]
access_token_secret = env_vars["twitter_access_token_secret"]

# OAuth process, using the keys and tokens
try:
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
except:
    print("Issue with Twitter API authentication")
    quit()

# Creation of the tweepy interface, using auth
api = tweepy.API(auth)

# Check people and pages until end date
users = {**env_vars["people"], **env_vars["pages"]}
name_dict = {users[x]["twitter"]: x for x in users}
end_date = datetime.datetime(
    env_vars["end_date"]["year"],
    env_vars["end_date"]["month"],
    env_vars["end_date"]["day"],
    0, 0, 0)
start_date = datetime.datetime(
    env_vars["start_date"]["year"],
    env_vars["start_date"]["month"],
    env_vars["start_date"]["day"],
    0, 0, 0) - datetime.timedelta(days=1)
collected_tweets = {}
num_tweets_found = 0

for user in users:
    account = users[user]["twitter"]
    if account is None: continue
    collected_tweets[user] = []
    try:
        for status in tweepy.Cursor(api.user_timeline, screen_name='@' + account,
                                    tweet_mode="extended").items():
            curr_tweet = Tweet(status._json, name_dictionary=name_dict)
            if curr_tweet.datetime > end_date: continue
            if curr_tweet.datetime < start_date: break
            collected_tweets[user].append(curr_tweet.jsonable())
            num_tweets_found += 1
    except Exception as e:
        print(e)
        print("Issue for " + user)

print(str(num_tweets_found) + " tweets found")
with open("found/found_tweets.json", 'w+') as output_file:
    json.dump(collected_tweets, output_file)

# IMPORTANT INFO ON RATE LIMIT:
# Every 20 tweets is a call, we have 900 calls per 15 minutes, 100,000 per day, 3200 per timeline max
# print(api.rate_limit_status())
