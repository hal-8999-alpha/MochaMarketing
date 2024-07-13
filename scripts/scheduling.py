# NEEDS the post, the platforms, schedule date, profile key

import os
import requests
from dotenv import load_dotenv
from update import update
import sys
import json
from datetime import datetime, timedelta
import random

def schedule_post(data):
    print("Scheduling")
    load_dotenv()

    # print("In Scheduling")
    # print(data)

    api_key = os.getenv("MOCHA_PINECONE_API_KEY")
    environment = os.getenv("MOCHA_PINECONE_API_ENV")
    index_name = os.getenv("MOCHA_PINECONE_API_INDEX")

    post = data["notes"]
    vectorId = data["postId"]
    platforms = ['facebook']
    date_string = data["date"]

    # Convert to datetime object
    date = datetime.strptime(date_string, "%Y-%m-%d")

    # Add a day to the date
    date = date + timedelta(days=1)

    # Generate a random hour and minute
    random_hour = random.randint(10, 18)
    random_minute = random.randint(0, 59)

    # If the hour is 18 (6 PM), ensure the minute is not more than 30
    if random_hour == 18:
        random_minute = random.randint(0, 30)

    # Change date and set time to the random hour and minute
    date_time = date.replace(hour=random_hour, minute=random_minute, second=0)

    # Convert back to string in the desired format
    formatted_date = date_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    profile_key = data["profileKey"]
    url = data.get("url", None)  # Use .get() to avoid KeyError if 'url' does not exist

    payload = {
        "post": post,
        "platforms": platforms,
        "scheduleDate": formatted_date,
        'profileKey': profile_key,
    }
    
    # If 'url' exists and is not None, add it to payload as 'mediaUrls'
    if url:
        payload['mediaUrls'] = [url]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ.get('AYRSHARE_API_KEY')}",
    }
    # print(f"Payload: {payload}")
    # print(f"Headers: {headers}")

    response = requests.post("https://app.ayrshare.com/api/post", json=payload, headers=headers)
    if response.status_code == 200:
        value = "No"
        vectorId = vectorId
        field = "Active"
        
        update(api_key, index_name, environment, value, vectorId, field)
        print("Complete")
        return response.json()
    else:
        # Extract response content
        error_content = response.text
        try:
            # Try to convert response content to JSON
            error_content = response.json()
        except json.JSONDecodeError:
            pass
        raise Exception(f"Failed to schedule post. Response status: {response.status_code}, Response content: {error_content}")
    
if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
    else:
        data = None
    schedule_post(data)

    



# (datetime.datetime.now() + datetime.timedelta(days=7 + times_through)).strftime("%Y-%m-%dT%H:%M:%S.000Z")