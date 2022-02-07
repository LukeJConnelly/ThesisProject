import json
from random import randint
from googlesearch import search
from time import sleep

env_file = open("env.json", 'r')
people = json.load(env_file)["people"]

# Collect all search results
found_google = {}
num_found_google = 0

for person in people:
    success = False
    while not success:
        try:
            found_google[person] = search(person + " public masterclass article insight speech class audience talk")
            num_found_google += len(found_google[person])
            success = True
        except:
            sleep(randint(30, 40))


print(str(num_found_google) + " google results found")
output_file = open("found_google.json", 'w')
json.dump(found_google, output_file)

quit()
