import json
import re
import math
import sys
import csv
import re
import random
import numpy as np
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support, plot_precision_recall_curve
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize


def get_probability(x, y):
    return (x + y) - (x * y)


def run_experiment(train_data, vectorizer):
    texts_train = [item['Text'] for item in train_data]
    y_train = [int(item['Label']) for item in train_data]
    x_train = vectorizer.fit_transform(texts_train)
    metric_to_result = tune_model(x_train, y_train)
    return metric_to_result


def tune_model(x_train, y_train):
    results = []
    for c in np.arange(0.1, 1.1, 0.1):  # regularisation parameter
        model = LogisticRegression(C=c).fit(x_train, y_train)
        assert model.classes_[1] == 1  # ensuring that positive class is at index 1
        for t in np.arange(0.1, 1, 0.1):  # classification threshold
            prec, rec, fscore = evaluate_model_with_threshold(model, x_train, y_train, t)
            result = {
                'c': c, 't': t,
                'prec': prec, 'rec': rec, 'fscore': fscore,
                'model': model
            }
            results.append(result)
    metric_to_best = {
        'prec': sorted(results, key=lambda item: item['prec'], reverse=True)[0],
        'rec': sorted(results, key=lambda item: item['rec'], reverse=True)[0],
        'fscore': sorted(results, key=lambda item: item['fscore'], reverse=True)[0],

    }
    return metric_to_best


def evaluate_model_with_threshold(model, x, y, threshold):
    assert model.classes_[1] == 1
    probs = model.predict_proba(x)
    probs = probs[:, 1]  # only positive-class probabilities
    pred = [(1 if p >= threshold else 0) for p in probs]
    prec, rec, fscore, _ = precision_recall_fscore_support(y, pred, labels=[0, 1], zero_division=0)
    prec, rec, fscore = prec[1], rec[1], fscore[1]  # only positive-class results
    return prec, rec, fscore


def get_feature_list(model, vectorizer):
    f_to_i = vectorizer.vocabulary_
    i_to_f = dict((i, f) for f, i in f_to_i.items())
    weights = model.coef_
    weighted_features = [(i_to_f[i], weights[0, i]) for i in range(weights.shape[1])]
    weighted_features.sort(key=lambda x: x[1], reverse=True)
    return weighted_features


def get_feature_weights(training_data, bound, ngram=1):
    vectorizer = TfidfVectorizer(stop_words='english', lowercase=True, ngram_range=(1, ngram))
    metric_to_result = run_experiment(training_data, vectorizer)
    result = metric_to_result['fscore']
    model = result['model']
    feature_list = get_feature_list(model, vectorizer)
    # Scale weights to range (-1, 1)
    max_weight = feature_list[0][1]
    min_weight = feature_list[-1][1]
    scalar = (bound / max_weight) if max_weight > abs(min_weight) else (-bound / min_weight)
    feature_weights = {}
    for f in feature_list:
        feature_weights[f[0]] = round(scalar * f[1], 2)
    return feature_weights


random.seed(42)

ngram = int(sys.argv[-3]) if sys.argv[:-1] else 3
bound = float(sys.argv[-2]) if sys.argv[:-1] else 0.95
word_bound = float(sys.argv[-1]) if sys.argv[:-1] else 0.6

training_data = json.load(open("twitter_training_data.json", 'r'))
is_epe = training_data["is_epe"]
is_training = training_data["is_training"]

found_tweets = json.load(open('../found/found_tweets.json'))
word_training_data = []
hashtag_training_data = []
user_mention_training_data = []

# Create training set
tweet_index = -1
for user in found_tweets:
    tweet_list = found_tweets[user]
    for tweet in tweet_list:
        tweet_index += 1
        hashtags = " ".join([hashtag["text"].lower() for hashtag in tweet["entities"]["hashtags"]])
        user_mentions = " ".join(
            [user_mention["screen_name"].lower() for user_mention in tweet["entities"]["user_mentions"]])
        if is_training[tweet_index]:
            word_training_data.append({'Text': tweet["cleaned_text"], 'Label': is_epe[tweet_index]})
            if hashtags: hashtag_training_data.append({'Text': hashtags, 'Label': is_epe[tweet_index]})
            if user_mentions: user_mention_training_data.append({'Text': user_mentions, 'Label': is_epe[tweet_index]})

word_final = get_feature_weights(word_training_data, word_bound, ngram=ngram)
# No need for ngrams as all hashtags and usernames are one word only
hashtag_final = get_feature_weights(hashtag_training_data, bound)
user_mention_final = get_feature_weights(user_mention_training_data, bound)

# ADAPTED FROM ANALYSIS.PY
# Collect features across all tweets
tweets_probability_users_dict = user_mention_final
tweets_probability_hashtags_dict = hashtag_final
tweets_probability_words_dict = word_final

tweet_index = -1
tweet_list_features = []
ps = PorterStemmer()
for user in found_tweets:
    tweet_list = found_tweets[user]
    for tweet in tweet_list:
        tweet_index += 1
        if not is_training[tweet_index]:
            continue
        features = []
        for user_mention in tweet["entities"]["user_mentions"]:
            if user_mention["screen_name"].lower() in tweets_probability_users_dict:
                features.append(("Mentions: " + user_mention["screen_name"].lower(),
                                 tweets_probability_users_dict[user_mention["screen_name"].lower()]))
        for hashtag in tweet["entities"]["hashtags"]:
            if hashtag["text"].lower() in tweets_probability_hashtags_dict:
                features.append(
                    ("Hashtag: " + hashtag["text"].lower(), tweets_probability_hashtags_dict[hashtag["text"].lower()]))
        word_tokens = word_tokenize(tweet["cleaned_text"])
        stems = [ps.stem(w) for w in word_tokens]
        for term in tweets_probability_words_dict:
            if all(x.lower() in stems for x in term.split(' ')):
                features.append(("Uses: " + term, tweets_probability_words_dict[term.lower()]))
        tweet_list_features.append((tweet_index, tweet["cleaned_text"], features))

# Calculate probability for each tweet given its features
results = []
for lf in tweet_list_features:
    if not lf[2]:
        results.append((lf[0], 0.1))
        continue
    probability = lf[2][0][1] if lf[2][0][1] > 0 else 1 + lf[2][0][1]
    for feature in lf[2][1:]:
        if feature[1] > 0:
            probability = get_probability(probability, feature[1])
        else:
            probability = 1 - get_probability(1 - probability, abs(feature[1]))
    results.append((lf[0], probability))

# Collect accuracy using results with various initial (i) and threshold (j) probabilities
accuracies = {}
i = 0.001
while i < 1:
    j = 0.001
    while j < 1:
        tp = 0
        tn = 0
        fp = 0
        fn = 0
        for r in results:
            p = get_probability(i, r[1])
            if is_epe[r[0]] and p > j:
                tp += 1
            elif is_epe[r[0]]:
                fn += 1
            elif p > j:
                fp += 1
            else:
                tn += 1
        # Accuracy when positive expected
        pacc = tp / (tp + fn) if tp + fn != 0 else 0
        # Overall accuracy
        acc = (tp + tn) / len(results)
        accuracies[(round(i, 3), round(j, 3))] = (pacc + acc) / 2
        j += 0.025
    i += 0.025

# Get best results for i and j
optimal_probabilities = max(accuracies, key=accuracies.get)

print("Best run " + str(accuracies[optimal_probabilities]) + " " + str(optimal_probabilities))

output_file = open("twitter_suggested_weights.json", 'w')
json.dump({"initial": optimal_probabilities[0],
           "threshold": optimal_probabilities[1],
           "users": user_mention_final,
           "hashtags": hashtag_final,
           "words": word_final},
          output_file)

quit()

