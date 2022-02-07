import json


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
)
Outputs EPE and non-EPE events to the relevant keys in output
"""


def outputfn(people_involved, type, short_summary, link, is_epe, output):
    output[type].append({"reference": short_summary, "result": is_epe})
    if is_epe:
        for person in people_involved:
            if not person in output["found_epe"]:
                output["found_epe"][person] = []
            output["found_epe"][person].append({
                "type": type,
                "person": person,
                "link": link
            })
        if not people_involved:
            output["unknown_epe"].append({
                "type": type,
                "link": link
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
    found_file = open('found_' + type + '.json')
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
        outputfn(people_involved, type, article["title"], article["link"], probability > 0, output)


output = {"status": {},
          "tweets": [],
          "insight_website": [],
          "brainstorm": [],
          "silicon_republic": [],
          "podcast": [],
          "found_epe": {},
          "unknown_epe": []}

people_file = open('env.json')
people = json.load(people_file)["people"]
tweets_working = insight_website_working = brainstorm_working = silicon_republic_working = podcast_working = True

try:
    # Tweets found by collect_tweets.py
    found_tweets = json.load(open('found_tweets.json'))
    # Load probabilities associated with features for tweets
    tweets_probability_weights_file = open('probability_weights_tweets.json')
    tweets_probability_weights = json.load(tweets_probability_weights_file)
    tweets_probability_users_dict = tweets_probability_weights["users"]
    tweets_probability_hashtags_dict = tweets_probability_weights["hashtags"]
    tweets_probability_words_dict = tweets_probability_weights["words"]
    for user in found_tweets:
        tweet_list = found_tweets[user]
        for tweet in tweet_list:
            probability = tweets_probability_weights["initial"]
            for user_mention in tweet["entities"]["user_mentions"]:
                if user_mention["screen_name"].lower() in tweets_probability_users_dict:
                    probability = get_probability(probability,
                                                  tweets_probability_users_dict[user_mention["screen_name"].lower()])
            for hashtag in tweet["entities"]["hashtags"]:
                if hashtag["text"].lower() in tweets_probability_hashtags_dict:
                    probability = get_probability(probability,
                                                  tweets_probability_hashtags_dict[hashtag["text"].lower()])
            for word in tweets_probability_words_dict:
                if word in tweet["cleaned_text"]:
                    probability = get_probability(probability, tweets_probability_words_dict[word.lower()])
            is_epe = probability > tweets_probability_weights["threshold"]
            # Output
            people_involved = []
            if is_epe:
                if not tweet["retweet"]:
                    people_involved.append(user)
                for person in people:
                    if person in tweet["cleaned_text"] and not person == user:
                        people_involved.append(person)
                if not people_involved and tweet["retweet_author"] in [p["twitter"] for p in people.values()]:
                    people_involved.append(tweet["retweet_author"])
            outputfn(people_involved,
                     "tweets",
                     tweet["cleaned_text"] + " Link: https://twitter.com/twitter/statuses/" + str(tweet["id"]),
                     "https://twitter.com/twitter/statuses/" + str(tweet["id"]),
                     is_epe,
                     output)
except:
    tweets_working = False

try:
    # Articles found by collect_insight_website.py
    found_insight_website = json.load(open('found_insight_website.json'))
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
        if is_epe:
            # Identify people involved in EPE
            for person in people:
                if person.lower() in (article["title"] + article["text"]).lower():
                    people_involved.append(person)
        outputfn(people_involved, "insight_website", article["title"], article["link"], is_epe, output)
except:
    insight_website_working = False

try:
    # Articles found by collect_brainstorm.py
    generic_article_analysis(people, "brainstorm", output)
except:
    brainstorm_working = False

try:
    # Articles found by collect_silicon_republic.py
    generic_article_analysis(people, "silicon_republic", output)
except:
    silicon_republic_working = False

try:
    # Articles found by collect_silicon_republic.py
    found_podcast = json.load(open('found_podcast.json'))
    for episode in found_podcast:
        probability = 0
        people_involved = []
        for person in people:
            if person.lower() in (episode["name"] + episode["description"]).lower():
                probability = 1
                people_involved.append(person)
        # Output
        outputfn(people_involved, "podcast", episode["name"], episode["link"], probability > 0, output)
except:
    podcast_working = False

# Export any exceptions thrown
output["status"] = {
    "tweets": tweets_working,
    "insight_website": insight_website_working,
    "brainstorm": brainstorm_working,
    "silicon_republic": silicon_republic_working,
    "podcast": podcast_working
}
print(output["status"])

output_file = open("output.json", 'w')
json.dump(output, output_file)

quit()
