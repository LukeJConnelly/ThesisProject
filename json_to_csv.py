import json
import csv
import os
if not os.path.exists('csv_outputs'):
    os.makedirs('csv_outputss')

output = json.load(open('output.json'))

for type in output["status"]:
    if output["status"][type]:
        file = open("csv_outputs/" + type + ".csv", 'w+')
        writer = csv.writer(file)
        for result in output[type]:
            writer.writerow([result["reference"], ("Yes" if result["result"] else "No")])
        file.close()

quit()
