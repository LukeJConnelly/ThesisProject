import json
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from dateutil.parser import parse
from datetime import datetime, timedelta
import magicdate
import re
import locationtagger
import traceback

similarity_thresholds = {
    ("article", "article"): 0.99,
    ("insight_website", "insight_website"): 0.99,
    ("podcast", "podcast"): 0.99,
    ("tweets", "tweets"): 0.98,
    ("article", "insight_website"): 0.99,
    ("article", "podcast"): 0.99,
    ("article", "tweets"): 0.99,
    ("insight_website", "podcast"): 0.97,
    ("insight_website", "tweets"): 0.97,
    ("podcast", "tweets"): 0.97
}


def get_probability(x, y):
    return (x + y) - (x * y)


"""
outputfn (
    people_involved - list of names,
    type - string representing source,
    short_summary - a way to identify the analysed piece,
    link - a link to the analysed piece,
    is_epe - whether this is EPE or not
    output - map with keys <type>, found_epe and unknown_epe
    full_text - entire text of piece, used to measure similarity
    details - location, date and audience details
)
Outputs EPE and non-EPE events to the relevant keys in output
"""


def outputfn(people_involved, type, short_summary, link, is_epe, output, full_text, details={}):
    output[type].append({"reference": short_summary, "result": is_epe})
    if is_epe:
        for person in people_involved:
            if not person in output["found_epe"]:
                output["found_epe"][person] = []
            output["found_epe"][person].append({
                "type": type,
                "person": person,
                "link": link,
                "details": details,
                "full_text": full_text
            })
        if not people_involved:
            output["unknown_epe"].append({
                "type": type,
                "link": link,
                "details": details,
                "full_text": full_text
            })


"""
generic_article_analysis (
    people - list of names,
    type - string representing articles' sources,
    output - map with keys <type>, found_epe and unknown_epe
)
Expects file named found_<type>.json
With list of objects with keys:
"text", "title" and "authors"
"""


def generic_article_analysis(people, type, output):
    found_file = open('found/found_' + type + '.json')
    found = json.load(found_file)
    for article in found:
        probability = 0
        people_involved = []
        for person in people:
            if person.lower() in (article["text"] + article["title"]).lower():
                probability = 1
                people_involved.append(person)
                continue
            for author in article["authors"]:
                if person.lower() in author.lower():
                    probability = 1
                    people_involved.append(person)
                    continue
        outputfn(people_involved, type, article["title"], article["link"],
                 probability > 0, output, article["title"] + ": " + article["text"],
                 details={"date": article["datetime"], "location": "online", "audience": audience_estimate[type]})


def estimate_date(default_date, text):
    date = default_date
    try:
        # Currently no support for x days/weeks/months ago
        search = re.search(
            '(today|tomorrow|yesterday)|((last|next) ('
            'mon|tue|wed|thu|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday|week|night)(?!(['
            'a-z]| of)))',
            text.lower())
        day_mention = search.group() if search else search
        if day_mention == "last week":
            date = date - timedelta(7)
        elif day_mention == "next week":
            date = date + timedelta(7)
        elif day_mention == "last night":
            date = date - timedelta(1)
        elif day_mention and "last" in day_mention:
            date = parse(day_mention.split(' ')[1], fuzzy=True, default=(date - timedelta(7)))
        elif day_mention:
            date = magicdate.magicdate(day_mention)
        elif not re.search("(?<!\d{3})\d(?!\d)", text):
            date = parse(text, fuzzy=True, default=date)
    except:
        pass
    return date


def estimate_location(text):
    place_entity = locationtagger.find_locations(text=text)
    location = {}
    if place_entity.other:
        location["place"] = place_entity.other[0]
    if place_entity.cities and place_entity.cities[0] not in location.values():
        location["city"] = place_entity.cities[0]
    if place_entity.regions and place_entity.regions[0] not in location.values():
        location["region"] = place_entity.regions[0]
    if place_entity.countries and place_entity.countries[0] not in location.values():
        location["country"] = place_entity.countries[0]
    return location if location.keys() and not set(location.keys()) == {"place"} else {}


output = {"status": {},
          "tweets": [],
          "insight_website": [],
          "brainstorm": [],
          "silicon_republic": [],
          "podcast": [],
          # "google": [],
          "found_epe": {},
          "unknown_epe": []}

env = json.load(open('env.json'))
people = env["people"]
pages = env["pages"]
audience_estimate = env["audience_estimate"]
tweets_working = insight_website_working = brainstorm_working = silicon_republic_working = podcast_working = True  # =
# google_working

try:
    # Tweets found by collect_tweets.py
    found_tweets = json.load(open('found/found_tweets.json'))
    # Load probabilities associated with features for tweets
    tweets_probability_weights_file = open('probability_weights_tweets.json')
    tweets_probability_weights = json.load(tweets_probability_weights_file)
    tweets_probability_users_dict = tweets_probability_weights["users"]
    tweets_probability_hashtags_dict = tweets_probability_weights["hashtags"]
    tweets_probability_words_dict = tweets_probability_weights["words"]
    ps = PorterStemmer()
    for user in found_tweets:
        tweet_list = found_tweets[user]
        for tweet in tweet_list:
            probability = tweets_probability_weights["initial"]
            features = []
            for user_mention in tweet["entities"]["user_mentions"]:
                if user_mention["screen_name"].lower() in tweets_probability_users_dict:
                    features.append(("Mentions: " + user_mention["screen_name"].lower(),
                                     tweets_probability_users_dict[user_mention["screen_name"].lower()]))
                    if tweets_probability_users_dict[user_mention["screen_name"].lower()] > 0:
                        probability = get_probability(probability, tweets_probability_users_dict[
                            user_mention["screen_name"].lower()])
                    else:
                        probability = 1 - get_probability(1 - probability, abs(
                            tweets_probability_users_dict[user_mention["screen_name"].lower()]))
            for hashtag in tweet["entities"]["hashtags"]:
                if hashtag["text"].lower() in tweets_probability_hashtags_dict:
                    features.append(("Hashtag: " + hashtag["text"].lower(),
                                     tweets_probability_hashtags_dict[hashtag["text"].lower()]))
                    if tweets_probability_hashtags_dict[hashtag["text"].lower()] > 0:
                        probability = get_probability(probability,
                                                      tweets_probability_hashtags_dict[hashtag["text"].lower()])
                    else:
                        probability = 1 - get_probability(1 - probability, abs(
                            tweets_probability_hashtags_dict[hashtag["text"].lower()]))
            word_tokens = word_tokenize(tweet["cleaned_text"])
            stems = [ps.stem(w) for w in word_tokens]
            for term in tweets_probability_words_dict:
                if all(x.lower() in stems for x in term.split(' ')):
                    features.append(("Uses: " + term, tweets_probability_words_dict[term.lower()]))
                    if tweets_probability_words_dict[term.lower()] > 0:
                        probability = get_probability(probability, tweets_probability_words_dict[term.lower()])
                    else:
                        probability = 1 - get_probability(1 - probability,
                                                          abs(tweets_probability_words_dict[term.lower()]))
            is_epe = probability > tweets_probability_weights["threshold"]
            # Output
            people_involved = []
            date = None
            location = None
            audience = audience_estimate["twitter"]
            if is_epe:
                if not tweet["retweet"] and user not in pages:
                    people_involved.append(user)
                for person in people:
                    if person in tweet["cleaned_text"]:
                        people_involved.append(person)
                if not people_involved and tweet["retweet_author"] in [p["twitter"] for p in people.values()]:
                    people_involved.append(tweet["retweet_author"])
                date = str(
                    estimate_date(datetime.strptime(tweet["datetime"], "%Y-%m-%d %H:%M:%S"), tweet["cleaned_text"]))
                location = estimate_location(tweet["original_text"])
                for key, value in audience_estimate["external"].items():
                    if key.lower() in str(tweet):
                        audience = value
                        break
            outputfn(people_involved,
                     "tweets",
                     tweet["cleaned_text"] + " Link: https://twitter.com/twitter/statuses/" + str(tweet["id"]),
                     "https://twitter.com/twitter/statuses/" + str(tweet["id"]),
                     is_epe,
                     output,
                     tweet["cleaned_text"],
                     details={"date": date, "location": location, "audience": audience})
except Exception:
    print("Tweets currently down with trace: ", traceback.format_exc())
    tweets_working = False

try:
    # Articles found by collect_insight_website.py
    found_insight_website = json.load(open('found/found_insight_website.json'))
    # Load probabilities associated with features for articles
    article_probability_weights_file = open('probability_weights_article.json')
    article_probability_weights = json.load(article_probability_weights_file)
    article_probability_words_dict = article_probability_weights["words"]
    for article in found_insight_website:
        probability = article_probability_weights["initial"]
        for word in article_probability_words_dict:
            if word in article["text"].lower():
                probability = get_probability(probability, article_probability_words_dict[word])
            if word in article["title"].lower():
                probability = get_probability(probability, get_probability(article_probability_words_dict[word],
                                                                           article_probability_words_dict[word]))
        # Output
        is_epe = probability > article_probability_weights["threshold"]
        people_involved = []
        date = None
        location = None
        audience = audience_estimate["insight_website"]
        if is_epe:
            # Identify people involved in EPE
            for person in people:
                if person.lower() in (article["title"] + article["text"]).lower():
                    people_involved.append(person)
            date = str(estimate_date(datetime.strptime(article["datetime"], "%Y-%m-%d %H:%M:%S%z"),
                                     article["title"] + ": " + article["text"]))
            location = estimate_location(article["title"] + ": " + article["text"])
            for key, value in audience_estimate["external"].items():
                if key.lower() in str(article):
                    audience = value
                    break
        outputfn(people_involved, "insight_website", article["title"] + " Link: " + article["link"], article["link"],
                 is_epe, output, article["title"] + ": " + article["text"],
                 details={"date": date, "location": location, "audience": audience})
except Exception:
    print("Insight Website currently down with trace: ", traceback.format_exc())
    insight_website_working = False

try:
    # Articles found by collect_brainstorm.py
    generic_article_analysis(people, "brainstorm", output)
except Exception:
    print("Brainstorm currently down with trace: ", traceback.format_exc())
    brainstorm_working = False

try:
    # Articles found by collect_silicon_republic.py
    generic_article_analysis(people, "silicon_republic", output)
except Exception:
    print("Silicon Republic currently down with trace: ", traceback.format_exc())
    silicon_republic_working = False

try:
    # Articles found by collect_podcast.py
    found_podcast = json.load(open('found/found_podcast.json'))
    for episode in found_podcast:
        probability = 0
        people_involved = []
        for person in people:
            if person.lower() in (episode["name"] + episode["description"]).lower():
                probability = 1
                people_involved.append(person)
        # Output
        outputfn(people_involved, "podcast", episode["name"], episode["link"],
                 probability > 0, output, episode["name"] + ": " + episode["description"],
                 details={"date": episode["datetime"], "location": "online", "audience": audience_estimate["podcast"]})
except Exception:
    print("Podcast currently down with trace: ", traceback.format_exc())
    podcast_working = False

# try:
#     # Articles found by collect_google.py
#     found_google = json.load(open('found/found_google.json'))
#     # Load probabilites associated with features
#     google_probability_weights_file = open('probability_weights_google.json')
#     google_probability_weights = json.load(google_probability_weights_file)
#     google_probability_words_dict = google_probability_weights["words"]
#     for person_searched in found_google:
#         results = found_google[person_searched]
#         for result in results:
#             probability = google_probability_weights["initial"]
#             for word in google_probability_words_dict:
#                 if word.lower() in result["text"].lower():
#                     probability = get_probability(probability, google_probability_words_dict[word])
#             is_epe = probability > google_probability_weights["threshold"]
#             people_involved = []
#             if is_epe:
#                 for person in people:
#                     if person.lower() in result["text"].lower():
#                         people_involved.append(person)
#             # Output
#             outputfn(people_involved, "google", result["link"], result["link"], is_epe, output)
# except Exception:
#     print("Google currently down with trace: ", traceback.format_exc())
#     google_working = False

# Export any exceptions thrown
output["status"] = {
    "tweets": tweets_working,
    "insight_website": insight_website_working,
    "brainstorm": brainstorm_working,
    "silicon_republic": silicon_republic_working,
    "podcast": podcast_working
    # ,"google": google_working
}
print(output["status"])

import spacy

nlp = spacy.load('en_core_web_lg')


def check_duplicates(output):
    all_events = []
    for p in output["found_epe"]:
        all_events += output["found_epe"][p]
    all_events += output["unknown_epe"]
    spacy_texts = [nlp(e["full_text"]) for e in all_events]
    similarities = [[0] * len(spacy_texts) for i in range(len(spacy_texts))]
    for i1, t1 in enumerate(spacy_texts):
        for i2, t2 in enumerate(spacy_texts):
            if i1 >= i2: continue
            similarities[i1][i2] = t1.similarity(t2)
    final_events = []
    output["duplicates"] = []
    for index, event in enumerate(all_events):
        duplicate = None
        for i, s in enumerate(similarities[index]):
            if index < i and s > similarity_thresholds[tuple(sorted([all_events[i]["type"], event["type"]]))]:
                if event["type"] == "podcast" or all_events[i]["type"] == "podcast":
                    m1 = re.search('(?:episode|ep|eps)(?:[.#,<>%~!:;]*\s*)*(\d+)', event["full_text"].lower())
                    m2 = re.search('(?:episode|ep|eps)(?:[.#,<>%~!:;]*\s*)*(\d+)', all_events[i]["full_text"].lower())
                    if m1 and m2 and int(m1.group(1)) - int(m2.group(1)) != 0: continue
                duplicate = all_events[i]
                if "person" in duplicate and "person" not in event:
                    event["person"] = duplicate["person"]
        if not duplicate:
            final_events.append(event)
        else:
            output["duplicates"].append([event["link"], duplicate["link"]])
    output["found_epe"] = {}
    output["unknown_epe"] = []
    for e in final_events:
        e.pop("full_text")
        if "person" in e:
            if e["person"] in output["found_epe"]:
                output["found_epe"][e["person"]].append(e)
            else:
                output["found_epe"][e["person"]] = [e]
        else:
            output["unknown_epe"].append(e)
    return output


slim_output = check_duplicates(output)

with open("output.json", 'w+') as output_file:
    json.dump(slim_output, output_file)

del slim_output["podcast"]
del slim_output["tweets"]
del slim_output["insight_website"]
del slim_output["brainstorm"]
del slim_output["silicon_republic"]
with open("EPE_"+datetime.now().strftime("%H-%M_%d-%m-%y")+".json", 'w+') as full_file:
    json.dump(slim_output, full_file)
