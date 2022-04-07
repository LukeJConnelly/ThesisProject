import newspaper
import datetime
import json

env_file = open("env.json", 'r')
env_vars = json.load(env_file)

start_date = datetime.datetime(
    env_vars["start_date"]["year"],
    env_vars["start_date"]["month"],
    env_vars["start_date"]["day"],
    0, 0, 0).replace(tzinfo=datetime.timezone.utc) - datetime.timedelta(days=1)

end_date = datetime.datetime(
    env_vars["end_date"]["year"],
    env_vars["end_date"]["month"],
    env_vars["end_date"]["day"],
    0, 0, 0).replace(tzinfo=datetime.timezone.utc)

silicon_republic_newspaper = newspaper.build('https://www.siliconrepublic.com/', memoize_articles=False)

try:
    with open("found/memory_silicon_republic.json", 'r') as memory_file:
        previous_articles = json.load(memory_file)
except:
    previous_articles = {}

for article in silicon_republic_newspaper.articles:
    article.download()
    article.parse()
    if article.text == "": continue
    if article.publish_date is None: continue
    previous_articles[article.url] = {
        "title": article.title,
        "text": article.text,
        "authors": article.authors,
        "link": article.url,
        "datetime": str(article.publish_date)
    }

collected_articles = []
delete_list = []
for k in previous_articles:
    art = previous_articles[k]
    d = datetime.datetime.strptime(art["datetime"], "%Y-%m-%d %H:%M:%S%z")
    if (datetime.datetime.now() - d.replace(tzinfo=None)).days > 365:
        delete_list.append(k)
    if d > end_date or d < start_date: continue
    collected_articles.append(art)

for k in delete_list: del previous_articles[k]

print(str(len(collected_articles)) + " silicon republic articles found")

with open("found/memory_silicon_republic.json", 'w+') as memory_file:
    json.dump(previous_articles, memory_file)

with open("found/found_silicon_republic.json", 'w+') as output_file:
    json.dump(collected_articles, output_file)
