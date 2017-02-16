import os
import traceback
import json
import requests
from datetime import datetime
from math import ceil

from flask import Flask, request
from flask_mongoengine import MongoEngine

from uber_rides.session import Session
from uber_rides.client import UberRidesClient
from uber_rides.errors import ClientError

from messages import get_message, search_keyword


session = Session(server_token=os.environ.get('UBER_SERVER_TOKEN'))
client = UberRidesClient(session)
token = os.environ.get('FB_ACCESS_TOKEN')
app = Flask(__name__)

app.config['MONGODB_SETTINGS'] = {
    'db': os.environ.get('MONGO_DB'),
    'host': os.environ.get('MONGO_HOST'),
    'username': os.environ.get('MONGO_USER'),
    'password': os.environ.get('MONGO_PASS'),
    'port': int(os.environ.get('MONGO_PORT'))
}

db = MongoEngine(app)


class Context(db.Document):
    user_id = db.LongField(required=True)
    context = db.StringField()
    start_point = db.PointField()
    end_point = db.PointField()
    seat_count = db.IntField()
    when = db.DateTimeField(default=datetime.now())



def location_quick_reply(sender, text=None):
    if not text:
        text = get_message('location-button')
    return {
        "recipient": {
            "id": sender
        },
        "message": {
            "text": text,
            "quick_replies": [
                {
                    "content_type": "location",
                }
            ]
        }
    }


def send_attachment(sender, type, payload):
    return {
        "recipient": {
            "id": sender
        },
        "message": {
            "attachment": {
                "type": type,
                "payload": payload,
            }
        }
    }


def send_text(sender, text):
    return {
        "recipient": {
            "id": sender
        },
        "message": {
            "text": text
        }
    }


def send_message(payload):
    requests.post('https://graph.facebook.com/v2.6/me/messages/?access_token=' + token, json=payload)


def estimate_price(user, seat_count, **kwargs):
    context = get_or_create_context(user)

    try:
        response = client.get_price_estimates(
            start_latitude=context.start_point['coordinates'][1],
            start_longitude=context.start_point['coordinates'][0],
            end_latitude=context.end_point['coordinates'][1],
            end_longitude=context.end_point['coordinates'][0],
            seat_count=seat_count
        )
    except ClientError as e:
        return {'error': str(e)}


    prices = response.json.get('prices')
    print(prices)

    estimates = ''
    for price in prices:
        duration = ceil(price['duration']/60)
        estimates = '{}\n{}: {} ({} min)'.format(estimates, 
                                        price['localized_display_name'], 
                                        price['estimate'],
                                        duration)

    return estimates


def get_or_create_context(user):
    context = Context.objects(user_id=user).first()
    if not context:
        context = Context(user_id=user, context='start').save()
    return context


def change_context(user, new_context):
    context = get_or_create_context(user)
    context.context = new_context
    context.save()


def define_location(user, latitude, longitude, status):
    context = get_or_create_context(user)
    if status == 'start':
        context.start_point = {'type': 'Point',
                               'coordinates': [longitude, latitude]}
    elif status == 'end':
        context.end_point = {'type': 'Point',
                             'coordinates': [longitude, latitude]}
    context.save()


@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        try:
            data = json.loads(request.data.decode())
            sender = data['entry'][0]['messaging'][0]['sender']['id']

            context = get_or_create_context(sender)

            # Get message
            if 'message' in data['entry'][0]['messaging'][0]:
                message = data['entry'][0]['messaging'][0]['message']

            # Starting conversation
            if context.context == 'start':
                text = message['text']

                # If text not in city list...
                chat_message = search_keyword(text)

                if chat_message:
                    # if found keyword, reply with chat stuff
                    message = send_text(sender, chat_message)
                    send_message(message)
                else:
                    payload = location_quick_reply(sender, get_message('pick-a-place'))
                    send_message(payload)
            
                    change_context(sender, 'start_location')

                return 'Ok'

            elif context.context in ['start_location', 'end_location']:
                if 'attachments' in message:
                    if 'payload' in message['attachments'][0]:
                        if 'coordinates' in message['attachments'][0]['payload']:
                            location = message['attachments'][0]['payload']['coordinates']
                            latitude = location['lat']
                            longitude = location['long']

                            if context.context == 'start_location':
                                define_location(sender, latitude=latitude, longitude=longitude, status='start')
                                change_context(sender, 'end_location')

                                payload = location_quick_reply(sender)
                                send_message(payload)
                            else:
                                define_location(sender, latitude=latitude, longitude=longitude, status='end')
                                estimate = estimate_price(sender, 2)

                                if 'error' in estimate:
                                    message = send_text(sender, estimate['error'])
                                    send_message(message)
                                    
                                    return 'Ok'

                                change_context(sender, 'start')

                                message = send_text(sender, get_message('estimate').format(estimate))
                                send_message(message)

                else:
                    text = message['text']

                    # If text not in city list...
                    chat_message = search_keyword(text)

                    if chat_message:
                        # if found keyword, reply with chat stuff
                        message = send_text(sender, chat_message)
                        send_message(message)
                    else:
                        payload = location_quick_reply(sender, get_message('pick-a-place'))
                        send_message(payload)


        except Exception as e:
            print(traceback.format_exc())
    elif request.method == 'GET':
        if request.args.get('hub.verify_token') == os.environ.get('FB_VERIFY_TOKEN'):
            return request.args.get('hub.challenge')
        return "Wrong Verify Token"
    return "Nothing"

if __name__ == '__main__':
    app.run(debug=True)
