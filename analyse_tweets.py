import json
from classes.tweet import Tweet

def get_probability(X, Y):
    return (X+Y)-(X*Y)

# Tweets found by collect_tweets.py
found_tweets_file = open('found_tweets.json')
found_tweets = json.load(found_tweets_file)

# Load probabilities associated with features
probability_weights_file = open('probability_weights.json')
probability_weights = json.load(probability_weights_file)
probability_users_dict = probability_weights["users"]
probability_hashtags_dict =  probability_weights["hashtags"]
probability_words_dict = probability_weights["hashtags"]

# Loop through tweets and output ones of high probability to be EPE
for tweet_list in found_tweets.values():
    for tweet_json in tweet_list:
        tweet = json.loads(tweet_json)
        probability = probability_weights["initial"]
        for user_mention in tweet['entities']['user_mentions']:
            if user_mention["screen_name"].lower() in probability_users_dict.keys() :
                probability = get_probability(probability, probability_users_dict[user_mention["screen_name"].lower()])
        for hashtag in tweet['entities']['hashtags']:
            if hashtag["text"].lower() in probability_hashtags_dict.keys() :
                probability = get_probability(probability, probability_hashtags_dict[hashtag["text"].lower()])
        # Prints all tweets as CSV with Yes/No
        if probability > probability_weights["threshold"]:
            print(tweet["original_text"].replace(',', ' ').replace('\n', ' ') + ", Yes")
        else:
            print(tweet["original_text"].replace(',', ' ').replace('\n', ' ') + ", No")

quit()