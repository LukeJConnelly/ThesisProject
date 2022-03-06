# Assumes running of wget https://www.rte.ie/brainstorm/ -r -E -p --no-parent --accept-regex ".*/brainstorm/20[0-9]{2}/.*"

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

curr_year = datetime.datetime.now().year
files = []

# Brainstorm stores articles as brainstorm/YEAR/article
# Loop through all years included in current search period
while curr_year >= env_vars["end_date"]["year"]:
    directory = "./www.rte.ie/brainstorm/" + str(curr_year)+"/"
    pathname = directory + "/**/**/index.html"
    files.extend(glob.glob(pathname))
    curr_year -= 1  

# Filter files by regex /<year>/<4 digit ID>/<article>/index.html
r = re.compile(r".(?:\\|/)www.rte.ie(?:\\|/)brainstorm(?:\\|/)20[0-9]{2}(?:\\|/)[0-9]{4}(?:\\|/).*(?:\\|/)index.html")
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
        "authors": article.authors[:-2],
        "link": f[2:],
        "datetime": str(article.publish_date)})
    
print(str(len(collected_articles)) + " brainstorm articles found")
output_file = open("found/found_brainstorm.json", 'w')
json.dump(collected_articles, output_file)