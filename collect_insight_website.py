# Assumes running of wget https://www.insight-centre.org/news/ -r -E -p

from newspaper import Article
import datetime
import glob
import json
import re
    
env_file = open("env.json", 'r')
env_vars = json.load(env_file)

end_date = datetime.datetime(
    env_vars["end_date"]["year"], 
    env_vars["end_date"]["month"],
    env_vars["end_date"]["day"], 
    0, 0, 0).replace(tzinfo=datetime.timezone.utc)

# All files matching insight-centre/<article>/index.html
pathname = "./www.insight-centre.org/**/index.html"
files = glob.glob(pathname)
r = re.compile("./www.insight-centre.org/*[a-z0-9-]{9,}/index.html")
files = list(filter(r.match, files))

collected_articles = []

for f in files:
    # Read and parse file using newspaper
    article = Article(f)
    with open(f, 'rb') as htmlf:
        html = htmlf.read()
    article.set_html(html)
    article.parse()
    if article.text == "": continue
    if article.publish_date == None or article.publish_date < end_date: continue
    collected_articles.append({
        "title": article.title,
        "text": article.text,
        "link": f[2:-10],
        "datetime": str(article.publish_date)
    })
    
print(str(len(collected_articles)) + " insight website articles found")
output_file = open("found_insight_website.json", 'w')
json.dump(collected_articles, output_file)

quit()