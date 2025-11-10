import os
import re
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime, timedelta

# Set up your Slack bot token and channel ID
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
CHANNEL_ID = "C09RMGFL55F"  # Replace with your actual channel ID

client = WebClient(token=SLACK_TOKEN)

def get_recent_messages():
    try:
        # Get messages from the last 7 days
        oldest = (datetime.now() - timedelta(days=7)).timestamp()
        response = client.conversations_history(channel=CHANNEL_ID, oldest=oldest)
        # Filter out messages that contain "Weekly Build Failure Summary"
        filtered_messages = [
            msg for msg in response['messages'] 
            if "Build Failure Summary (Last 7 Days)" not in msg.get('text', '')
        ]
        return filtered_messages
    except SlackApiError as e:
        print(f"Error fetching messages: {e.response['error']}")
        return []

def extract_failed_builds(messages):
    failed_builds = {}
    for msg in messages:
        text = msg.get('text', '')
        if "Failed" in text:  # Adjust this to match your TeamCity message format
            build_name, build_link = extract_build_name_and_link(text)
            if build_name in failed_builds:
                failed_builds[build_name]['count'] += 1
                # Update link to the most recent failure
                if build_link:
                    failed_builds[build_name]['link'] = build_link
            else:
                failed_builds[build_name] = {'count': 1, 'link': build_link}
    return failed_builds

def extract_build_status_and_name(text):
    # Match status and build name (without version)
    match = re.search(r"(Failed|Succeeded) - (.+?) #\d+\.\d+\.\d+", text)
    if match:
        status = match.group(1)
        name = match.group(2).strip()
        return status, name
    return None, None

def get_build_statuses(messages):
    build_statuses = {}

    for msg in messages:
        text = msg.get('text', '')
        status, name = extract_build_status_and_name(text)
        if status and name:
            # Always overwrite with the latest status seen
            build_statuses[name] = status

    return build_statuses

def get_failed_builds(build_statuses):
    return {name for name, status in build_statuses.items() if status == "Failed"}

def extract_build_name_and_link(text):
    # Extract build name
    build_name_match = re.search(r"Failed - (.+?) #\d+\.\d+\.\d+", text)
    build_name = build_name_match.group(1).strip() if build_name_match else "Unknown Build"

    # Extract TeamCity link (assuming it's in angle brackets like <https://teamcity/...>)
    link_match = re.search(r"<(https?://[^>]+)>", text)
    build_link = link_match.group(1) if link_match else None
    return build_name, build_link

def generate_summary(messages, failed_builds):
    summary = "<!channel> *🔴 Build Failure Summary (Last 7 Days)*\n\n"
    for msg in messages:
        text = msg.get('text', '')
        status, name = extract_build_status_and_name(text)
        if status == "Failed" and name in failed_builds:
            # Extract link if present
            link_match = re.search(r"<(https?://[^>]+)>", text)
            link = link_match.group(1) if link_match else None
            if link:
                summary += f":warning: *<{link}|{name}>*\n\n"
            else:
                summary += f":warning: *{name}*\n\n"
    return summary

def post_summary(failed_builds):
    summary = "<!channel> *🔴 Build Failure Summary (Last 7 Days)*\n"
    
    for build_name, build_info in failed_builds.items():
        count = build_info['count']
        link = build_info['link']
        if link:
            # summary += f":warning: - <{link}|*{build_name}*>: {count} failure(s)\n"
            summary += f":warning: - <{link}>: {count} failure(s)\n"
        else:
            summary += f"- {build_name}: {count} failure(s)\n"
    
    try:
        client.chat_postMessage(channel=CHANNEL_ID, text=summary)
    except SlackApiError as e:
        print(f"Error posting summary: {e.response['error']}")

# Run the workflow
messages = get_recent_messages()
failed_builds = extract_failed_builds(messages)
print(failed_builds)
post_summary(failed_builds)

#messages = get_recent_messages()
#build_statuses = get_build_statuses(messages)
#failed_builds = get_failed_builds(build_statuses)
#summary = generate_summary(messages, failed_builds)
#post_summary(summary)
