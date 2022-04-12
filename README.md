# EPE Tracker Tool FYP

The EPE Tracker Tool is designed to pull data from a variety
of sources in order to automatically identify potential EPE 
events. Currently supported sources are: Twitter, Insight 
Centre website, RTÉ Brainstorm, Silicon Republic and Spotify
podcasts.

Note: While referring to multiple files I will occasionally use [variable]_file.txt syntax. 
If variable in this context was "podcast" this refers to the relevant podcast_file.txt

## Requirements

There are no requirements to run this online - read the instructions and
run through Google Colab here: https://colab.research.google.com/drive/1_06Yg007qp3vs4CAaSrNDWg5B7acf0wW

If you wish to run or develop this offline you will require:

- Python 3.x
- Bash (if training)
- Jupyter Notebook (if running from notebook locally)
- Python modules/libraries as specified in the Jupyter Notebook and requirements.txt/requirements.py 

## Instructions for online use (User)

Ensure you have been added as a user or have a valid sign in to
an authorised user.

Upload: 
- analysis.py
- Every collect_[type].py
- env.json,
- probability_weights_tweets.json
- probability_weights_article.json

To the top level of your user's Google Drive

If you have not been provided with an env.json, probability_weights_tweets.json, or probability_weights_article.json
file check your Google Drive as they may already be present and correct. If they are not present,
rename the [file you need].sample file to remove the .sample suffix and upload it to Google Drive.
Use the UI to configure.

If you have been provided with a link to the UI visit it there and log in.
If not you can host it for yourself locally using `python3 -m http.server`

Update the running details visible in the UI as desired before running as specified in the Google Colab.
The output from your run will be visible from the UI and be stored in your Google Drive permanently as
EPE_[timestamp].json. The UI will display the latest output, to
view a previous output you can open the EPE_[timestamp].json file and copy its contents to here: https://codebeautify.org/jsonviewer

## Instructions for offline use (User)

Ensure env.json, probability_weights_tweets.json, probability_weights_article.json are present in root directory and set values appropriately.

At this point the user can:
- Install python/module requirements using `pip install -r requirements.txt` followed by `python3 requirements.py`, then run every collect_[type].py file before running analysis.py

or

- Run the Jupyter Notebook

At this point, regardless of approach, output will be in both output.json and EPE_[timestamp].json. 

To view interactive json I recommend copying and pasting to https://codebeautify.org/jsonviewer 

## Instructions for training

Training can be performed on either tweets or insight website articles.

Run the suitable collect_[type].py file to collect a sufficiently large number
of training examples. 

Read through these examples and fill in the array is_epe in
the [type]_training_data.json file. The is_training array should be used to determine whether
the corresponding example is included in the training or not. 

Generally you want to train on all your examples so this should consist of all true values.
However if you wish to evaluate your results leave 30% of these randomly false. An example on
how this can be done is visible in split_tweets_by_time.py

Once the file is populated run [type]_learn_weights.py, optionally you can add arguments as specified at the top of each file.

If you wish to further tweak the accuracy you can run the .sh files to discover optimum arguments. Beware of overfitting and local minima.

At the end of this the recommended values are specified in [type]_suggested_weights.json

## Instructions for new setup (Developer)

Create env.json, probability_weights_article.json and probability_weights_tweets.json
files. Examples of the structures of these files are provided in [file_name].sample
and explanations can be seen in the Jupyter Notebook

Sign up to the Twitter and Spotify APIs and provide the keys in env.json

If external to Insight you can remove the Insight phase from analysis.py and the Jupyter Notebook
or rewrite the wget requests and directory traversal in insight_website.py to match a website of your own choosing

Setup complete. Follow the online or offline instructions to use

### Created by Luke Connelly (lukejconnelly1@gmail.com)