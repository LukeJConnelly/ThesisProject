import re
import emoji
import wordninja
import datetime


class Tweet:
    id = None
    datetime = datetime.datetime.now()
    original_text = ""
    cleaned_text = ""
    author = {
        "id": None,
        "username": "",
        "display_name": ""
    }
    entities = {
        "hashtags": [],
        "user_mentions": [],
        "urls": [],
        "media": []}
    retweet = False
    retweet_author = {
        "id": None,
        "username": "",
        "display_name": ""}
    quote = False
    quoted_text = ""

    def jsonable(self):
        return {
            "id": self.id,
            "datetime": str(self.datetime),
            "original_text": self.cleaned_text,
            "cleaned_text": self.cleaned_text,
            "author": dict(self.author),
            "entities": dict(self.entities),
            "retweet": self.retweet,
            "retweet_author": dict(self.retweet_author),
            "quote": self.quote,
            "quoted_text": self.quoted_text
        }

    def wordify(_, hashtag):
        if sum(1 for c in hashtag if c.isupper()) > 1:
            return re.sub(r'([a-z](?=[A-Z])|[A-Z](?=[A-Z][a-z]))', r'\1 ', hashtag)
        if len(hashtag) <= 4:
            return hashtag.upper()
        return ' '.join(wordninja.split(hashtag))

    def clean_text(self, name_dictionary={}):
        cleaned_text = self.original_text
        # Remove hashtags
        for hashtag in self.entities['hashtags']:
            cleaned_text = cleaned_text[:cleaned_text.index("#" + hashtag["text"])] + " " + self.wordify(
                hashtag["text"]) + " " + cleaned_text[
                                         cleaned_text.index("#" + hashtag["text"]) + len("#" + hashtag["text"]):]
        # Remove links
        for url in self.entities['urls']:
            if url["url"] in cleaned_text:
                cleaned_text = cleaned_text[:cleaned_text.index(url["url"])] + "." + cleaned_text[cleaned_text.index(
                    url["url"]) + len(url["url"]):]
        # Remove media
        for media in self.entities['media']:
            if media["url"] in cleaned_text:
                cleaned_text = cleaned_text[:cleaned_text.index(media["url"])] + "." + cleaned_text[cleaned_text.index(
                    media["url"]) + len(media["url"]):]
        # Remove RT
        if self.retweet:
            cleaned_text = re.sub('RT @[A-Za-z0-9_]+:', '', cleaned_text)
        # Remove @'s
        cleaned_text = re.sub('.@', '@', cleaned_text)
        for user_mention in self.entities['user_mentions']:
            if user_mention["screen_name"].lower() in cleaned_text.lower():
                name_to_use = user_mention["name"]
                if user_mention["screen_name"] in name_dictionary:
                    name_to_use = name_dictionary[user_mention["screen_name"]]
                cleaned_text = cleaned_text[:cleaned_text.lower().index(
                        "@" + user_mention["screen_name"].lower()
                    )]\
                    + " " + name_to_use + ", " \
                    + cleaned_text[cleaned_text.lower().index(
                        "@" + user_mention["screen_name"].lower())
                        + len("@" + user_mention["screen_name"]):]
        # Remove emojis and special chars
        cleaned_text = ''.join(c for c in cleaned_text if c not in emoji.UNICODE_EMOJI['en'])
        cleaned_text = re.sub('&amp;', '&', cleaned_text) + '.'
        # Clean up grammar issues created by cleaning
        cleaned_text = re.sub('([\.\,]|\s)+(?=[\?\.\!\:\,\)\'\"])', '', cleaned_text)
        return re.sub(',\s*,|[.]\s*[.]|:\s*[.]|\s+', ' ', cleaned_text)
        # Ongoing considerations:
        # - REMOVE SMILEY FACES LIKE :)?
        # - ONLY ADD , WITH @ IF CHAR AFTER IS @?
        # - ADD CONTEXT TO QUOTE TWEETS?

    def __init__(self, tweepy_tweet=None, name_dictionary={}):
        if tweepy_tweet:
            self.id = tweepy_tweet['id']
            self.author['id'] = tweepy_tweet['user']['id']
            self.author['username'] = tweepy_tweet['user']['screen_name']
            self.author['display_name'] = tweepy_tweet['user']['name']
            if 'retweeted_status' in tweepy_tweet.keys():
                self.retweet = True
                self.original_text = re.sub('https://t.co/[A-Za-z0-9]+$', '',
                                            tweepy_tweet['retweeted_status']['full_text'])
                self.datetime = datetime.datetime.strptime(tweepy_tweet['retweeted_status']['created_at'],
                                                           '%a %b %d %H:%M:%S +0000 %Y')
                self.entities['hashtags'] = tweepy_tweet['retweeted_status']['entities']['hashtags']
                self.entities['user_mentions'] = tweepy_tweet['retweeted_status']['entities']['user_mentions']
                self.entities['urls'] = tweepy_tweet['retweeted_status']['entities']['urls']
                self.entities['media'] = tweepy_tweet['retweeted_status']['entities']['media'] if 'media' in \
                                                                                                  tweepy_tweet[
                                                                                                      'retweeted_status'][
                                                                                                      'entities'].keys() else []
                self.retweet_author['id'] = tweepy_tweet['retweeted_status']['user']['id']
                self.retweet_author['username'] = tweepy_tweet['retweeted_status']['user']['screen_name']
                self.retweet_author['display_name'] = tweepy_tweet['retweeted_status']['user']['name']
                self.retweeted_text = tweepy_tweet['full_text']
            else:
                self.retweet = False
                self.datetime = datetime.datetime.strptime(tweepy_tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
                self.original_text = tweepy_tweet['full_text']
                self.entities['hashtags'] = tweepy_tweet['entities']['hashtags']
                self.entities['user_mentions'] = tweepy_tweet['entities']['user_mentions']
                self.entities['urls'] = tweepy_tweet['entities']['urls']
                self.entities['media'] = tweepy_tweet['entities']['media'] if 'media' in tweepy_tweet[
                    'entities'].keys() else []
            self.quote = tweepy_tweet['is_quote_status']
            self.quoted_text = tweepy_tweet['quoted_status'][
                'full_text'] if 'quoted_status' in tweepy_tweet.keys() else ''
            self.cleaned_text = self.clean_text()
