import logging
import os

from flask import Flask, render_template
from flask_ask import Ask, statement, question
import requests


app = Flask(__name__)
ask = Ask(app, "/")
logging.getLogger('flask_ask').setLevel(logging.DEBUG)


# General Helpers

def _get_credentials():
    credentials_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', 'watsonCredentials.json'))
    with open(credentials_path, 'r') as file_pointer:
        return tuple(file_pointer.read().splitlines())


def _watson_tone_api(text, credentials):
    ENDPOINT = 'https://gateway.watsonplatform.net/tone-analyzer/api/v3/tone'
    data = requests.get(ENDPOINT, auth=credentials, params={
        'text': text,
        'tones': 'emotion',
        'sentences': False,
        'version': '2017-08-16'
    }).json()
    return data


# Intent Handlers


@ask.intent('AnalyzeToneIntent')
def handle_analyze_tone(text):
    credentials = _get_credentials()
    results = _watson_tone_api(text, credentials).get(
        'document_tone', {}).get('tone_categories', [])

    if results:
        emotions = results[0].get('tones')
        if emotions:
            best_match = max(emotions, key=lambda x: x['score'])
            emotion_name = best_match.get('tone_name')
            emotion_score = best_match.get('score') * 100
            if emotion_name and emotion_score:
                speech_text = render_template('emotion', name=emotion_name,
                                              score=emotion_score)
                return statement(speech_text)

    speech_text = render_template('error')
    return statement(speech_text)


# Event Handlers

@ask.launch
@ask.intent('AMAZON.HelpIntent')
def instructions():
    speech_text = render_template('instructions')
    return question(speech_text).reprompt(speech_text)


@ask.intent('AMAZON.CancelIntent')
@ask.intent('AMAZON.StopIntent')
def stop():
    speech_text = render_template('stop')
    return statement(speech_text)


@ask.session_ended
def session_ended():
    return '{}', 200


if __name__ == '__main__':
    if 'ASK_VERIFY_REQUESTS' in os.environ:
        verify = str(os.environ.get('ASK_VERIFY_REQUESTS', '')).lower()
        if verify == 'false':
            app.config['ASK_VERIFY_REQUESTS'] = False
    app.run(debug=True)
