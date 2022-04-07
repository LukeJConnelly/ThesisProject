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


def test_model(training_data, test_data, ngram=1):
    vectorizer = TfidfVectorizer(stop_words='english', lowercase=True, ngram_range=(1, ngram))
    metric_to_result = run_experiment(training_data, vectorizer)
    result = metric_to_result['fscore']
    return result["model"], vectorizer


random.seed(42)

ngram = int(sys.argv[-1]) if sys.argv[:-1] else 3

training_data = json.load(open("twitter_training_data.json", 'r'))
is_epe = training_data["is_epe"]
is_training = training_data["is_training"]

found_tweets = json.load(open('../found/found_tweets.json'))
word_training_data = []
hashtag_training_data = []
user_mention_training_data = []
word_test_data = []
hashtag_test_data = []
user_mention_test_data = []

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
            hashtag_training_data.append({'Text': hashtags, 'Label': is_epe[tweet_index]})
            user_mention_training_data.append({'Text': user_mentions, 'Label': is_epe[tweet_index]})
        word_test_data.append({'Text': tweet["cleaned_text"], 'Label': is_epe[tweet_index]})
        hashtag_test_data.append({'Text': hashtags, 'Label': is_epe[tweet_index]})
        user_mention_test_data.append({'Text': user_mentions, 'Label': is_epe[tweet_index]})

word_model, word_vectorizer = test_model(word_training_data, word_test_data, ngram=ngram)
# No need for ngrams as all hashtags and usernames are one word only
hashtag_model, hashtag_vectorizer = test_model(hashtag_training_data, hashtag_test_data)
user_mention_model, user_mention_vectorizer = test_model(user_mention_training_data, user_mention_test_data)

x_test_word = word_vectorizer.transform([item['Text'] for item in word_test_data])
x_test_hashtag = hashtag_vectorizer.transform([item['Text'] for item in hashtag_test_data])
x_test_user_mention = user_mention_vectorizer.transform([item['Text'] for item in user_mention_test_data])
y_test = [item['Label'] for item in word_test_data]

threshold = 0.1
tp = 0
tn = 0
fp = 0
fn = 0
word_probs = word_model.predict_proba(x_test_word)[:, 1]
hashtag_probs = hashtag_model.predict_proba(x_test_hashtag)[:, 1]
user_mention_probs = user_mention_model.predict_proba(x_test_user_mention)[:, 1]
results = []
for i in range(0, len(word_probs)):
    prediction = (word_probs[i] + hashtag_probs[i] + user_mention_probs[i]) / 3
    if y_test[i] and prediction > threshold:
        tp += 1
    elif y_test[i]:
        fn += 1
    elif prediction > threshold:
        fp += 1
    else:
        tn += 1
    results.append((word_test_data[i]["Text"], prediction > threshold))
# Accuracy when positive expected
pacc = tp / (tp + fn) if tp + fn != 0 else 0
# Overall accuracy
acc = (tp + tn) / len(word_probs)
print("Accuracy was " + str((pacc + acc) / 2))

file = open("model_test.csv", 'w+')
writer = csv.writer(file)
for result in results:
    writer.writerow([result[0], ("Yes" if result[1] else "No")])
file.close()

quit()
