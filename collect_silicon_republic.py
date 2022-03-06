import newspaper
import datetime
import json

env_file = open("env.json", 'r')
env_vars = json.load(env_file)

end_date = datetime.datetime(
    env_vars["end_date"]["year"],
    env_vars["end_date"]["month"],
    env_vars["end_date"]["day"],
    0, 0, 0).replace(tzinfo=datetime.timezone.utc)

silicon_republic_newspaper = newspaper.build('https://www.siliconrepublic.com/', memoize_articles=False)

collected_articles = []

for article in silicon_republic_newspaper.articles:
    article.download()
    article.parse()
    if article.text == "": continue
    if article.publish_date is None or article.publish_date < end_date: continue
    collected_articles.append(
        {"title": article.title,
         "text": article.text,
         "authors": article.authors,
         "link": article.url,
         "datetime": str(article.publish_date)})

print(str(len(collected_articles)) + " silicon republic articles found")

# Check if previous running is still before end date
try:
    output_file = open("found_silicon_republic.json")
    previous_articles = json.load(output_file)
    if datetime.datetime.strptime(previous_articles[-1]["datetime"], "%Y-%m-%d %H:%M:%S%z") > end_date:
        for previous_article in previous_articles:
            collected_articles.append(previous_article)
except: pass

output_file = open("found_silicon_republic.json", 'w')
json.dump(collected_articles, output_file)

quit()
