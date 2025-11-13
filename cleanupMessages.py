import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Set up your Slack bot token and channel ID
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
CHANNEL_ID = "C09RMGFL55F"  # Replace with your actual channel ID

client = WebClient(token=SLACK_TOKEN)

def delete_message(channel_id, message_ts):
    try:
        response = client.chat_delete(channel=channel_id, ts=message_ts)
        print("Message deleted:", response)
    except SlackApiError as e:
        print(f"Error deleting message: {e.response['error']}")

def cleanup_bot_messages(channel_id):
    response = client.conversations_history(channel=channel_id)
    for msg in response['messages']:
        if msg.get('bot_id'):  # Only delete bot messages
            delete_message(channel_id, msg['ts'])

cleanup_bot_messages(CHANNEL_ID)
