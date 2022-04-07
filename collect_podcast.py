import json
import datetime
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

env_file = open("env.json", 'r')
env_vars = json.load(env_file)

# Consumer keys and access tokens, used for OAuth
consumer_id = env_vars["spotify_client_id"]
access_secret = env_vars["spotify_client_secret"]

# Auth process using tokens
try:
    auth_manager = SpotifyClientCredentials(consumer_id, access_secret)
    spotify_api = spotipy.Spotify(auth_manager=auth_manager)
except:
    print("Issue with Spotify API authentication")

start_date = datetime.datetime(
    env_vars["start_date"]["year"],
    env_vars["start_date"]["month"],
    env_vars["start_date"]["day"],
    0, 0, 0) - datetime.timedelta(days=1)
end_date = datetime.datetime(
    env_vars["end_date"]["year"],
    env_vars["end_date"]["month"],
    env_vars["end_date"]["day"],
    0, 0, 0)
podcast_id = env_vars["podcast_id"]

# API call for podcast here
insight_podcast = spotify_api.show(podcast_id, market='IE')

# Collect all episodes up until cut off date
found_episodes = []
for ep in insight_podcast["episodes"]["items"]:
    ymd = ep["release_date"].split("-")
    release_date = datetime.datetime(int(ymd[0]),
                                     int(ymd[1]),
                                     int(ymd[2]),
                                     0, 0, 0)
    if release_date < start_date or release_date > end_date: continue
    found_episodes.append({"name": ep["name"],
                           "description": ep["description"],
                           "link": ep["external_urls"]["spotify"],
                           "datetime": str(release_date)})

print(str(len(found_episodes)) + " podcast episodes found")
with open("found/found_podcast.json", 'w') as output_file:
    json.dump(found_episodes, output_file)