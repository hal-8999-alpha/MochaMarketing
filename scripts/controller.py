# controller.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from getPineconeData import get_pinecone_data
from createCloudFolder import create_cloudinary_folder
from update import update
from dotenv import load_dotenv
from getDays import get_days
from flask.json import JSONEncoder
import numpy as np
from createCloudSign import generate_cloudinary_signature
from GoogleCalendar import get_calendar_events
from GmailRead import get_unread_messages_last_message
from createClientSampleString import upsert_content_to_pinecone
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import requests
from datetime import datetime
from airtable import Airtable
import subprocess
import json
import random
import string
import os
from cryptography.fernet import Fernet
from base64 import urlsafe_b64decode, urlsafe_b64encode
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.send']

# Functions and Classes

def run_secondary_task(data):
    task_type = data["type"]
    # print(task_type)

    creds = get_google_credentials()
    
    # Automated Approval
    task_mapping = {
        "Meeting": ["scripts/GmailSend.py", "scripts/scrapeAllText.py", "scripts/createCompanyProfile.py"],
        "Profile": ["scripts/createCalendarYear.py"],
        "Year": ["scripts/createCalendarQuarter.py"],
        "Quarter": ["scripts/createCalendarMonth.py"],
        "Month": ["scripts/createNextThirtyDays.py"],
        "Day": ["scripts/GmailSend.py"],
        "Post": ["scripts/scheduling.py"],
        "Auto": ["scripts/scrapeAllText.py", "scripts/createCompanyProfile.py", "scripts/createCalendarYear.py", "scripts/createCalendarQuarter.py", "scripts/createCalendarMonth.py", "scripts/createNextThirtyDays.py"]
    }

    # # Micromanaged Approval 
    # task_mapping = {
    #     "Meeting": ["GmailSend.py", "scrapeAllText.py", "createCompanyProfile.py"],
    #     "Profile": ["createCalendarYear.py", "GmailSend.py"],
    #     "Year": ["createCalendarQuarter.py" "GmailSend.py"],
    #     "Quarter": ["createCalendarMonth.py", "GmailSend.py"],
    #     "Month": ["createNextThirtyDays.py", "GmailSend.py"],
    #     # "Day": ["scheduling.py", "createNextThirtyDays.py", "GmailSend.py"],
    #     "Post": ["scheduling.py"],
    #     "Auto": ["scrapeAllText.py", "createCompanyProfile.py", "createCalendarYear.py", "createCalendarQuarter.py", "createCalendarMonth.py", "createNextThirtyDays.py"]
    # }

    data_json = json.dumps(data)
    creds_json = creds.to_json()
    
    if task_type in task_mapping:
        for script in task_mapping[task_type]:
            if "scripts/GmailSend.py" in script:
                result = subprocess.run(["python", script, data_json, creds_json], check=True)
            else:
                result = subprocess.run(["python", script, data_json], check=True)
                
            if result.returncode != 0:
                raise Exception(f"Failed to execute {script} script")

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.ndarray, np.generic)):
            return obj.tolist()
        elif hasattr(obj, '__html__'):
            html_method = getattr(obj, '__html__')
            if callable(html_method):
                return str(html_method())
            return str(html_method)
        return super(CustomJSONEncoder, self).default(obj)

def get_google_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=5001, prompt='consent')
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def create_process(data):
    api_key = os.environ.get("AIRTABLE_API_KEY")
    airtable_url = "https://api.airtable.com/v0/appQQYcFGySgy2qUu/tblSck0dGPShkhiv1"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    fields = {
        "type": data["type"],
        "companyId": data["companyId"],
        "company": data["company"],
        "notes": data["notes"],
        "isApproved": "false",
        "email": data["email"] if "email" in data else "",
    }
    
    if data["type"] == "Day" and "posts" in data:
        fields["postIds"] = json.dumps(data["posts"])

    payload = {
        "fields": fields
    }

    response = requests.post(airtable_url, headers=headers, json=payload)

    if response.status_code == 200:
        return "Refresh"
    else:
        raise Exception("Failed to create process")

def parse_date(date):
    for fmt in ('%m/%d/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(date, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError('no valid date format found')

def create_follow_up(data):
    lead = data['lead']
    date = data['date']
    complete = data['complete']
    notes = data['notes']
    
    # Convert date to ISO format
    date_iso = parse_date(date)

    # print("514")
    # print(date_iso)

    # Store your API Key in .env file
    api_key = os.environ.get("AIRTABLE_API_KEY")
    airtable_url = "https://api.airtable.com/v0/appQQYcFGySgy2qUu/tblRTJJfY8nB1ab5f"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    record_data = {
        "records": [
            {
                "fields": {
                    "notes": notes,
                    "title": lead,
                    "date": date_iso,
                    "isComplete": complete,
                    "url": data["url"] if "url" in data else "",
                    "postId": data["postId"] if "postId" in data else "",
                    "companyId": data["companyId"] if "companyId" in data else "",
                    # "platforms": data["platforms"] if "platforms" in data else "",    
                }
            }
        ]
    }
    # print(record_data)

    response = requests.post(airtable_url, json=record_data, headers=headers)

    return response

app = Flask(__name__)
CORS(app)
app.json_encoder = CustomJSONEncoder

# ROUTES

@app.route('/data', methods=['POST'])
def get_data():
    try:
        Id = request.json.get('Id')
        Type = request.json.get('Type')

        # print(Id)
        # print(Type)

        if not Id or not Type:
            return jsonify({"error": "Id and Type are required.", "success": False}), 400

        load_dotenv()

        api_key = os.getenv("MOCHA_PINECONE_API_KEY")
        environment = os.getenv("MOCHA_PINECONE_API_ENV")
        index_name = os.getenv("MOCHA_PINECONE_API_INDEX")

        script_path = "scripts/getPineconeData.py"
        result = subprocess.run(
            ["python", script_path, api_key, environment, index_name, str(Id), str(Type)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise Exception(f"Error executing getPineconeData.py: {result.stderr.strip()}")

        return jsonify({"success": True, "data": json.loads(result.stdout)}), 200

    except Exception as error:
        print("Error:", str(error))
        return jsonify({"error": str(error), "success": False}), 500
    
@app.route('/days', methods=['POST'])
def get_next_seven():
    try:
        calendar_id = request.json.get('calendarId')

        load_dotenv()

        api_key = os.getenv("MOCHA_PINECONE_API_KEY")
        environment = os.getenv("MOCHA_PINECONE_API_ENV")
        index_name = os.getenv("MOCHA_PINECONE_API_INDEX")

        json_data = get_days(api_key, environment, index_name, calendar_id)

        return jsonify({"success": True, "data": json_data}), 200

    except Exception as error:
        print("Error:", str(error))
        return jsonify({"error": str(error), "success": False}), 500
    
@app.route('/dayData', methods=['POST'])
def get_day_data():
    try:
        # Retrieve the Id and "Day" strings from the request body
        data = request.json
        calendarId = data.get('calendarId')
        Days = data.get('Days')

        # print(calendarId)
        # print(Days)

        if not calendarId:
            return jsonify({"error": "Id is required.", "success": False}), 400

        load_dotenv()

        api_key = os.getenv("MOCHA_PINECONE_API_KEY")
        environment = os.getenv("MOCHA_PINECONE_API_ENV")
        index_name = os.getenv("MOCHA_PINECONE_API_INDEX")

        script_path = "scripts/getDays.py"

        # Convert the list of "Day" strings to a comma-separated string
        day_string = ','.join(Days) if Days else None

        command = ["python", script_path, api_key, environment, index_name, str(calendarId)]
        if day_string:
            command.append(day_string)

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise Exception(f"Error executing getDays.py: {result.stderr.strip()}")

        return jsonify({"success": True, "data": json.loads(result.stdout)}), 200

    except Exception as error:
        print("Error:", str(error))
        return jsonify({"error": str(error), "success": False}), 500 


@app.route('/processes', methods=['POST'])
def create_process_endpoint():
    try:
        data = request.get_json()

        run_secondary_task(data)
        return jsonify({"success": True, "message": "Process created successfully"}), 200
    except Exception as error:
        print("Error:", str(error))
        return jsonify({"error": str(error), "success": False}), 500

@app.route('/processes', methods=['GET'])
def get_processes():
    try:
        type_filter = request.args.get("type")
        id_filter = request.args.get("companyId")

        api_key = os.environ.get("AIRTABLE_API_KEY")
        airtable_url = "https://api.airtable.com/v0/appQQYcFGySgy2qUu/tblSck0dGPShkhiv1"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        response = requests.get(airtable_url, headers=headers)

        if response.status_code == 200:
            airtable_data = response.json()
            process_data = []

            today = datetime.now().date()

            for record in airtable_data["records"]:
                if "isApproved" in record["fields"]:
                    is_approved = record["fields"]["isApproved"]
                    if "false" in is_approved:
                        process = {
                            "id": record["id"],
                            "notes": record["fields"]["notes"],
                            "dateCreated": record["fields"]["dateCreated"],
                            "lastModified": record["fields"]["lastModified"],
                            "isApproved": is_approved,
                            "type": record["fields"]["type"],
                            "company": record["fields"]["company"],
                            "companyId": record["fields"]["companyId"]
                        }
                        
                        if "postIds" in record["fields"]:
                            post_ids = json.loads(record["fields"]["postIds"])
                            process["postIds"] = post_ids

                        if (not type_filter or process["type"] == type_filter) and (not id_filter or process["companyId"] == id_filter):
                            process_data.append(process)

            return jsonify({"success": True, "data": process_data}), 200

        else:
            return jsonify({"error": "Failed to retrieve follow-up records", "success": False}), 500
    except Exception as error:
        print("Error:", str(error))
        return jsonify({"error": str(error), "success": False}), 500

@app.route('/forgot', methods=['POST'])
def forgot():
    data = request.get_json()
    encryptedEmail = data['email']
    normalEmail = data['base']
    api_key = os.environ.get("AIRTABLE_API_KEY")
    airtable_url = f"https://api.airtable.com/v0/appQQYcFGySgy2qUu/tblFVrtFqmuscDS8W?filterByFormula=SEARCH('{encryptedEmail}',email)"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.get(airtable_url, headers=headers)
    if response.status_code == 200:
        records = response.json()['records']
        if records:
            record_id = records[0]['id']
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            airtable_url = f"https://api.airtable.com/v0/appQQYcFGySgy2qUu/tblFVrtFqmuscDS8W/{record_id}"
            payload = {
                "fields": {
                    "temp": temp_password
                }
            }
            response = requests.patch(airtable_url, headers=headers, json=payload)
            if response.status_code == 200:
                email_data = {"type": "Password", "email": normalEmail, "temp_password": temp_password}
                creds = get_google_credentials()
                data_json = json.dumps(email_data)
                creds_json = creds.to_json()
                subprocess.run(["python", "scripts/GmailSend.py", data_json, creds_json], check=True)
                # subprocess.Popen(["python", "GmailSend.py", json.dumps(email_data), json.dumps(creds_info)])
                return {"status": "success"}, 200
    return {"status": "failed"}, 400

@app.route('/processes', methods=['PUT'])
def update_process():
    try:
        data = request.get_json()
        # print(data)

        task_type = data.get("type")
        # print(task_type)
        
        if not data or not task_type:
            return jsonify({"error": "Missing required fields", "success": False}), 400

        if task_type != "Meeting" and task_type != "Auto":
            if not data.get("id") or not data.get("isApproved") or not data.get("companyId") or not data.get("company"):
                return jsonify({"error": "Missing required fields", "success": False}), 400

            api_key = os.environ.get("AIRTABLE_API_KEY")
            airtable_url = f"https://api.airtable.com/v0/appQQYcFGySgy2qUu/tblSck0dGPShkhiv1/{data['id']}"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "fields": {
                    "type": data["type"],
                    "isApproved": data["isApproved"],
                }
            }

            response = requests.patch(airtable_url, headers=headers, json=payload)

            if response.status_code != 200:
                return jsonify({"error": "Failed to update process", "success": False}), 500
        # print("Made it to 378 before run_secondary")
        run_secondary_task(data)
        return jsonify({"success": True, "message": "Process updated successfully"}), 200

    except Exception as error:
        print("Error:", str(error))
        return jsonify({"error": str(error), "success": False}), 500

@app.route('/followup', methods=['GET'])
def get_followup():
    try:
        # Store your API Key in .env file
        api_key = os.environ.get("AIRTABLE_API_KEY")
        airtable_url = "https://api.airtable.com/v0/appQQYcFGySgy2qUu/tblRTJJfY8nB1ab5f"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        response = requests.get(airtable_url, headers=headers)

        if response.status_code == 200:
            airtable_data = response.json()
            follow_up_data = []

            today = datetime.now().date()

            for record in airtable_data["records"]:
                date = datetime.strptime(record["fields"].get("date", ""), "%Y-%m-%d").date()
                is_complete = record["fields"].get("isComplete", "")

                # if is_complete == "false":
                if is_complete == "false" and date <= today:
                    follow_up_data.append({
                        "id": record["id"],
                        "notes": record["fields"].get("notes", ""),
                        "title": record["fields"].get("title", ""),
                        "date": record["fields"].get("date", ""),
                        "isComplete": is_complete,
                        "companyId": record["fields"].get("companyId", ""),
                        "profileKey": record["fields"].get("profileKey", ""),
                        "postId": record["fields"].get("postId", ""),
                        "platforms": record["fields"].get("platforms", ""),
              })
                    
            # print(follow_up_data)

            return jsonify({"success": True, "data": follow_up_data}), 200
        else:
            return jsonify({"error": "Failed to retrieve follow-up records", "success": False}), 500
    except Exception as error:
        print("Error:", str(error))
        return jsonify({"error": str(error), "success": False}), 500
    
@app.route('/followup', methods=['PUT'])
def update_followup():
    from datetime import datetime
    import datetime
    try:
        data = request.json
        follow_up_id = data['id']
        is_complete = data['isComplete']

        # print(follow_up_id)
        # print(is_complete)

        # Store your API Key in .env file
        api_key = os.environ.get("AIRTABLE_API_KEY")
        airtable_url = f"https://api.airtable.com/v0/appQQYcFGySgy2qUu/tblRTJJfY8nB1ab5f/{follow_up_id}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "fields": {
                "isComplete": is_complete
            }
        }

        response = requests.patch(airtable_url, headers=headers, json=payload)

        if response.status_code == 200:
            # Check if 'profileKey' is in data and add 'type': 'Day' if true
            if 'profileKey' in data:
                data['type'] = 'Post'
                run_secondary_task(data)
            return jsonify({"success": True, "message": "Follow-up updated successfully"}), 200
        else:
            return jsonify({"error": "Failed to update follow-up", "success": False}), 500
    except Exception as error:
        print("Error:", str(error))
        return jsonify({"error": str(error), "success": False}), 500

@app.route('/followup', methods=['DELETE'])
def delete_followup():
    from datetime import datetime
    import datetime
    
    try:
        data = request.json
        follow_up_id = data['id']

        # Store your API Key in .env file
        api_key = os.environ.get("AIRTABLE_API_KEY")
        airtable_url = f"https://api.airtable.com/v0/appQQYcFGySgy2qUu/tblRTJJfY8nB1ab5f/{follow_up_id}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        response = requests.delete(airtable_url, headers=headers)

        if response.status_code == 200:
            return jsonify({"success": True, "message": "Follow-up deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete follow-up", "success": False}), 500
    except Exception as error:
        print("Error:", str(error))
        return jsonify({"error": str(error), "success": False}), 500

@app.route('/followup', methods=['POST'])
def followup_endpoint():
    try:
        data = request.json
        # print("549")
        # print(data)

        response = create_follow_up(data)

        if response.status_code == 200:
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "Failed to create follow-up record", "success": False}), 500
    except Exception as error:
        print("Error:", str(error))
        return jsonify({"error": str(error), "success": False}), 500

@app.route('/delete_email', methods=['POST'])
def delete_email_endpoint():
    try:
        email_id = request.json['email_id']
        creds = get_google_credentials()
        delete_email(creds, email_id)
        return jsonify({"success": True}), 200
    except Exception as error:
        print("Google error:", str(error))
        return jsonify({"error": str(error), "success": False}), 500

def delete_email(credentials, email_id):
    api_endpoint = f"https://gmail.googleapis.com/gmail/v1/users/me/threads/{email_id}/trash"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {credentials.token}"
    }
    response = requests.post(api_endpoint, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to delete email with ID {email_id}. Response: {response.text}")
    return response.json()

@app.route('/calendar', methods=['GET'])
def calendar_endpoint():
    try:
        creds = get_google_credentials()
        events = get_calendar_events(creds)
        return jsonify({"events": events, "success": True}), 200
    except Exception as error:
        return jsonify({"error": str(error), "success": False}), 500

@app.route('/connect_social_account', methods=['POST'])
def connect_social_account_endpoint():
    load_dotenv()

    API_KEY = os.getenv('AYRSHARE_API_KEY')
    with open('mochamarketing.key') as f:
        privateKey = f.read()

    try:
        profile_key = request.json.get('profile_key')
        if not profile_key:
            raise ValueError("Profile key is required")

        payload = {'domain': 'mochamarketing',
                   'privateKey': privateKey,
                   'profileKey': profile_key}
        headers = {'Content-Type': 'application/json',
                   'Authorization': f'Bearer {API_KEY}'}

        r = requests.post('https://app.ayrshare.com/api/profiles/generateJWT',
                          json=payload,
                          headers=headers)

        response = r.json()
        return jsonify({"response": response, "success": True}), 200

    except Exception as error:
        return jsonify({"error": str(error), "success": False}), 500

@app.route('/create-social-profile', methods=['POST'])
def create_ayrshare_profile():
    try:
        company_name = request.json.get('company_name')

        if not company_name:
            return jsonify({"error": "Company name is required", "success": False}), 400

        load_dotenv()
        import os

        API_KEY = os.getenv('AYRSHARE_API_KEY')
        if not API_KEY:
            return jsonify({"error": "Ayrshare API key not found", "success": False}), 500

        payload = {
            'title': company_name,
            'disabledSocial': ['pinterest', 'reddit', 'telegram', 'gmb']
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {API_KEY}'
        }

        r = requests.post('https://app.ayrshare.com/api/profiles/profile',
                          json=payload,
                          headers=headers)

        if r.status_code != 200:
            return jsonify({"error": "Failed to create Ayrshare profile", "success": False}), 500

        return jsonify({"profile": r.json(), "success": True}), 200
    except Exception as error:
        return jsonify({"error": str(error), "success": False}), 500

@app.route('/unread_messages', methods=['GET'])
def unread_messages_endpoint():
    try:
        creds = get_google_credentials()
        unread_messages = get_unread_messages_last_message(creds)
        if unread_messages:
            return jsonify({"unread_messages": unread_messages, "success": True}), 200
        else:
            return jsonify({"error": "No unread messages were found.", "success": False}), 404
    except Exception as error:
        return jsonify({"error": f"An error occurred: {str(error)}", "success": False}), 500

@app.route('/signature', methods=['POST'])
def signature_endpoint():
    try:
        data = request.get_json()
        if not data or "timestamp" not in data:
            return jsonify({"error": "Timestamp is required"}), 400

        # Extract the timestamp from the request body
        timestamp = data["timestamp"]

        # Generate the signature using the timestamp
        signature = generate_cloudinary_signature(timestamp)
        return jsonify({"signature": signature}), 200

    except Exception as error:
        return jsonify({"error": str(error), "success": False}), 500

@app.route('/create_cloud_folder', methods=['POST'])
def create_cloud_folder_route():
    try:
        data = request.get_json()
        if not data or "folderName" not in data:
            return jsonify({"error": "Folder name is required"}), 400

        folder_name = data["folderName"]
        result = create_cloudinary_folder(folder_name)
        if result:
            return jsonify({"error": result}), 500
        else:
            return jsonify({"success": True}), 200

    except Exception as error:
        return jsonify({"error": str(error), "success": False}), 500

@app.route('/sample', methods=['POST'])
def process_sample():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Text is required"}), 400

    try:
        output_file = upsert_content_to_pinecone(data["text"], data["id"])
        return jsonify({"output_file": output_file, "success": True}), 200
    except Exception as error:
        return jsonify({"error": str(error), "success": False}), 500

@app.route('/update', methods=['POST'])
def update_route():
    try:
        data = request.get_json()
        if not data:
            raise ValueError("Invalid JSON input")
        
        print(data)

        required_fields = ["value", "vectorId", "field"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        api_key = os.getenv("MOCHA_PINECONE_API_KEY")
        environment = os.getenv("MOCHA_PINECONE_API_ENV")
        index_name = os.getenv("MOCHA_PINECONE_API_INDEX")

        update(api_key, index_name, environment,
               data["value"], data["vectorId"], data["field"])
        return jsonify({"success": True}), 200

    except Exception as error:
        return jsonify({"error": str(error), "success": False}), 500
    
if __name__ == '__main__':
    app.run(debug=True)
