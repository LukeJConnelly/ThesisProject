# Currently unsupported

import json
from random import randint
from googlesearch import search
from time import sleep
from newspaper import Article
import requests
import re
import textract
import urllib3
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'


def download(url, file_name):
    response = requests.get(url)
    extension = ".html"
    if "pdf" in response.headers["Content-Type"]:
        extension = ".pdf"
    with open(file_name+extension, "wb") as file:
        file.write(response.content)
    return extension


env_file = open("env.json", 'r')
people = json.load(env_file)["people"]

# Collect all search results
found_google = {}
num_found_google = 0
file_name_regex = re.compile('[^a-zA-Z]')

for person in people:
    success = 0
    while not success > 0:
        try:
            success += 1
            found_google[person] = []
            found_results = search(person + " public masterclass article insight speech class audience talk")
            for result in found_results:
                if "xml" in result.lower():
                    continue
                try:
                    extension = download(result, "google_downloads/" + file_name_regex.sub('', result))
                    text = textract.process("google_downloads/" + file_name_regex.sub('', result)+extension)
                    found_google[person].append({
                        "link": result,
                        "text": text.decode('utf-8'),
                    })
                except Exception as e:
                    print(e)
            success = 5
            num_found_google += len(found_google[person])
        except Exception as e:
            print(e)
            sleep(randint(30, 40))

print(str(num_found_google) + " google results found")
with open("found/found_google.json", 'w') as output_file:
    json.dump(found_google, output_file)
