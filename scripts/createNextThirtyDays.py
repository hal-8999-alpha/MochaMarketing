import pinecone
from dotenv import load_dotenv
import os
import openai
import sys
import json
from controller import create_process, create_follow_up
import random
import time
from datetime import date, datetime
import re

# def write_summary_to_file(summary, file_name):
#     with open(file_name, 'w') as file:
#         file.write(summary)
#     print(f"Summary written to {file_name}")

def failed(data, notes):
    Id = data.get("companyId")
    today = date.today()
    formatted_date = today.strftime('%Y-%m-%d')
    complete = "false"
    title = "Day Failed " + Id

    newData = {
        "lead": title,
        "date": formatted_date, 
        "complete": complete,
        "notes": notes
    }

    create_follow_up(newData)

# NEEDS REWORKED

def validate_summary(summary):
    """Validate the format of the summary."""
    # Define the expected headlines
    expected_headlines = ["Id", "Active", "Approved", "Day", "Company", "Calendar Id", "Type", "Platform", "Content", "Additional Instructions", "Url"]

    # Check each headline
    for headline in expected_headlines:
        # Check if the headline is in the summary
        if headline not in summary:
            # print(f"Missing headline: {headline}")
            return False

        # Check if the headline is followed by a colon
        if not re.search(f"{headline}: ", summary):
            # print(f"Missing colon after headline: {headline}")
            return False

    # Check if there are any other headlines
    for line in summary.split('\n'):
        headline = line.split(': ')[0]
        if headline not in expected_headlines:
            # print(f"Unexpected headline: {headline}")
            return False

    # If all checks passed, return True
    return True


def rewrite_summary(summary):
    """Rewrite the summary in the correct format using OpenAI's GPT-4."""
    # print("Rewriting Summary")
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    MAX_RETRIES = 5
    for attempt in range(MAX_RETRIES):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are given a company summary that needs to be rewritten in the correct format. The correct format contains 11 headlines. The headlines are named Id, Active, Approved, Day, Company, Calendar Id, Type, Platform, Content, Additional Instructions, Url. Each headline is followed by a colon and its corresponding content."},
                    {"role": "user", "content": f"Please rewrite the following summary in the correct format: {summary}"},
                ]
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            if attempt < MAX_RETRIES - 1:  # i.e. not on last attempt
                print(f"Attempt {attempt+1} failed, retrying in 2 seconds.")
                time.sleep(2)  # wait for 2 seconds before retrying
                continue
            else:
                print(f"Attempt {attempt+1} failed, giving up.")
                print(f"Error: {str(e)}")
                return None

def get_which_day(api_key, environment, index_name, Id, Type):

    pinecone.init(api_key=api_key, environment=environment)

    # Connect to the index
    index = pinecone.Index(index_name=index_name)

    # Define the query vector (you may need to adjust the dimension and values)
    query_vector = [0] * 1536  

    query_result = index.query(
        vector=query_vector,
        filter={'$and': [
            {'Id': {'$eq': Id}},
            {'Type': {'$eq': "Month"}},
            {'Active': {'$eq': 'Yes'}},
            # {'Approved': {'$eq': 'Yes'}}
        ]},
        top_k=100,
        include_metadata=True
    )

    # print(query_result)

    if query_result and query_result["matches"][0]["metadata"]['Type'] == "Month":
        # Check if Active and Approved are "Yes"
        if query_result["matches"][0]['metadata']['Active'] == "Yes":
            # Extract the current quarter key and value
            current_day_key = query_result["matches"][0]['metadata']['Current Day']
            current_day_value = query_result["matches"][0]['metadata'][current_day_key]

            # print(current_quarter_value)
            return current_day_value
        # else:
        #     print("The record is not active and/or approved")
    else:
        print("No matching data found")

    # print(query_result["matches"][0]["metadata"])

def create_day_post(company_name, current_day, profile, client_sample, calendar_id, Id, idea, platform):
    # print("Generating Content")
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    MAX_RETRIES = 5
    for attempt in range(MAX_RETRIES):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are an expert at creating social media posts for consumer facing coffee brands."},
                    {"role": "user", "content": f"""Design a social media post for a single day. Use the CLIENT SAMPLE, PROFILE and IDEA to help you craft your post. The post should be formatted exactly as follows (use a colon and space after each headline):

            Id: {Id}
            Active: Yes
            Approved: No
            Day: {current_day}
            Company: {company_name}
            Calendar Id: {calendar_id}
            Type: Day
            Platform: {platform}
            Content: [The actual post content related to the IDEA. The post should end with a period]
            Additional Instructions: [Additional instructions for the human, if any]
            Url: None

        The Id, Active, Approved, Day, Company, Calendar Id, Type, Platform, and Url fields are ABSOLUTE and should be filled exactly as specified. The Content and Additional Instructions fields are CREATIVE and should be filled based on your expertise, the provided IDEA, and the COMPANY PROFILE. The post should be engaging.

        COMPANY PROFILE: {profile}
        IDEA: {idea}
        SAMPLE: {client_sample}
        """},
                ]
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            if attempt < MAX_RETRIES - 1:  # i.e. not on last attempt
                print(f"Attempt {attempt+1} failed, retrying in 2 seconds.")
                time.sleep(2)  # wait for 2 seconds before retrying
                continue
            else:
                print(f"Attempt {attempt+1} failed, giving up.")
                print(f"Error: {str(e)}")
                return None

def get_company_profile(api_key, environment, index_name, Id):
    pinecone.init(api_key=api_key, environment=environment)

    # Connect to the index
    index = pinecone.Index(index_name=index_name)

    # Define the query vector (you may need to adjust the dimension and values)
    query_vector = [0] * 1536  
    
    query_result = index.query(
        vector=query_vector,
        filter={'$and': [
            # {'company': {'$eq': '71830'}},
             {'Id': {'$eq': Id}},
             {'Type': {'$eq': "Profile"}},
            # {'Active': {'$eq': 'Yes'}},
        ]},
        top_k=100,
        include_metadata=True
    )

    # print(query_result)
    return query_result

def build_company_profile(matches):
    metadata = matches["matches"][0]['metadata']
    
    id = metadata['Id']
    company = metadata['Company']
    profile_type = metadata['Type']
    services = metadata['Services']
    mission = metadata['Mission']
    competitive_advantage = metadata['Competitive']
    values = metadata['Values']
    target_market = metadata['Target']
    platforms = metadata['Platforms']
    active = metadata['Active']

    profile = (
        f"Id: {id}\n"
        f"Company: {company}\n"
        f"Type: {profile_type}\n"
        f"Services: {services}\n"
        f"Mission: {mission}\n"
        f"Competitive Advantage: {competitive_advantage}\n"
        f"Values: {values}\n"
        f"Target Market: {target_market}\n"
        f"Platforms: {platforms}\n"
        f"Promotions: \n"
        f"Active: {active}"
    )

    return profile

## I Left this one the same but Year, Month and Quarter have a different version ###
def response_to_dict(response):
    # print(response)
    try:
        # FIRST
        lines = response.strip().split('\n')

        result = {}
        current_key = ""
        for line in lines:
            if not line.strip():
                continue
            key, value = line.split(':', 1)
            if key == "Company":
                # Add the company name to the result
                result[key.strip()] = value.split()[0]
                # Split the value string into separate key-value pairs
                pairs = value.split()[1:]
                for pair in pairs:
                    if ':' in pair:  # Make sure the pair contains a colon before splitting
                        sub_key, sub_value = pair.split(':', 1)
                        result[sub_key.strip()] = sub_value.strip()
                        current_key = sub_key.strip()
                    elif current_key:  # Make sure current_key has been set before appending
                        # Append the remaining value to the current key
                        result[current_key] += f" {pair.strip()}"
            else:
                result[key.strip()] = value.strip()

        # Remove leading and trailing spaces from all values
        for key, value in result.items():
            result[key] = value.strip()

    except:
        # SECOND
        lines = response.strip().split('\n')

        result = {}
        for line in lines:
            if not line.strip():
                continue

            if ':' not in line:
                # print(f"Warning: Skipping line due to missing colon: {line}")
                if 'Content' in result:
                    result['Content'] += f" {line}"
                else:
                    result['Content'] = line
                continue

            key, value = line.split(':', 1)
            key = key.strip()

            if key in ["Active", "Approved", "Id", "Day", "Calendar Id", "Type", "Company", "Content"]:
                result[key] = value.strip()
            else:
                if 'Content' not in result:
                    result['Content'] = ""
                result['Content'] += f" {key}: {value.strip()}"

    return result

# THIS WILL CURRENTLY ONLY GET ONE SAMPLE
def get_client_sample(api_key, environment, index_name, Id):
    
    pinecone.init(api_key=api_key, environment=environment)

    # Connect to the index
    index = pinecone.Index(index_name=index_name)

    # Define the query vector (you may need to adjust the dimension and values)
    query_vector = [0] * 1536  

    query_result = index.query(
        vector=query_vector,
        filter={'$and': [
            {'Id': {'$eq': Id}},
            {'Type': {'$eq': "Sample"}},
        ]},
        top_k=1,
        include_metadata=True
    )

    # Return the sample if found, otherwise return an empty string
    if len(query_result["matches"]) > 0:
        sample = query_result["matches"][0]["metadata"]["Content"]
        return sample
    else:
        return ""


def get_calendar_id(api_key, environment, index_name, Id):
    
    pinecone.init(api_key=api_key, environment=environment)

    # Connect to the index
    index = pinecone.Index(index_name=index_name)

    # Define the query vector (you may need to adjust the dimension and values)
    query_vector = [0] * 1536  

    query_result = index.query(
        vector=query_vector,
        filter={'$and': [
            {'Id': {'$eq': Id}},
            {'Type': {'$eq': "Month"}},
            {'Active': {'$eq': 'Yes'}},
            # {'Approved': {'$eq': 'Yes'}}
        ]},
        top_k=1,
        include_metadata=True
    )

    # print(query_result["matches"][0]["id"])
    id = query_result["matches"][0]["id"]
    return id

def get_current_day(api_key, environment, index_name, calendar_id):

    
    pinecone.init(api_key=api_key, environment=environment)

    # Connect to the index
    index = pinecone.Index(index_name=index_name)

    # print(calendar_id)
    
    result = index.fetch([calendar_id])

    # print(result)
    # current_day = result["vectors"][calendar_id]["metadata"]["Current Day"]
    current_day = result["vectors"][calendar_id]["metadata"]["Current Day"]
    # print(current_day)

    return(current_day)

def update_current_day(api_key, index_name, environment, current_day, Id):
    
    import datetime

    pinecone.init(
        api_key=api_key,
        environment=environment
    )

    index = pinecone.Index(index_name)

    query_vector = [0] * 1536  

    query_result = index.query(
        vector=query_vector,
        filter={'$and': [
            {'Type': {'$eq': "Month"}},
            {'Id': {'$eq': Id}},
            {'Active': {'$eq': "Yes"}}
        ]},
        top_k=1,
        include_metadata=True
    )

    calendarId = query_result["matches"][0]["id"]

    day_number = int(current_day.strip("Day ")) + 1
    updated_day = f"Day {day_number}"

    if day_number == 31:
        index.update(id=calendarId, set_metadata={"Current Day": updated_day, "Active": "No"})
        # Set the date to 20 days from today
        today = datetime.date.today() + datetime.timedelta(days=20)
        formatted_date = today.strftime('%Y-%m-%d')

        # Create the follow-up
        complete = "false"
        title = "Generate Month " + Id
        notes = Id

        newData = {
        "lead": title,
        "date": formatted_date, 
        "complete": complete,
        "notes": notes
        }
        # print("Sending Data to Generate Month Follow Up")
        # print(newData)

        create_follow_up(newData)
    else:
        index.update(id=calendarId, set_metadata={"Current Day": updated_day})

    # print("Updated")

def upsert_post(api_key, environment, index_name, refinedPost, Id, max_retries=5, sleep_interval=5):
    # Set the OpenAI API key
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Concatenate all the key-value pairs into a single string
    full_text = " ".join(f"{key}: {value}" for key, value in refinedPost.items() if key != "Id")

    # print("Starting Embeddings...")

    # Attempt to create the embedding, handling RateLimitError
    for attempt in range(max_retries):
        try:
            embedded_text = openai.Embedding.create(
                input=full_text,
                model="text-embedding-ada-002"
            )
            break
        except openai.error.RateLimitError as e:
            if attempt < max_retries - 1:  # i.e. not the last attempt
                print(e)
                print(f"Attempt {attempt+1} failed. Retrying in {sleep_interval} seconds...")
                time.sleep(sleep_interval)
                continue
            else:  # on the last attempt, re-raise the exception
                raise
    else:
        raise Exception(f"Failed to create embedding after {max_retries} attempts")

    # print("Embeddings Complete!")
    # print("Uploading to Pinecone...")

    # Attempt to initialize Pinecone and upload the embedding
    try:
        pinecone.init(
            api_key=api_key,
            environment=environment
        )

        index = pinecone.Index(index_name)

        random_number = str(random.randint(100000000000000, 999999999999999))

        pinecone_id = Id + '_post_'+ random_number

        # Create a single embedding with metadata
        embedding = {
            'id': pinecone_id,
            'values': embedded_text['data'][0]['embedding'],
            'metadata': refinedPost
        }

        # Call index.upsert() with the single embedding
        index.upsert([embedding])
    except Exception as e:
        print("An error occurred while uploading to Pinecone:")
        print(e)
        raise

    # print("Success uploading embeddings to Pinecone.")
    # print("\n")
    return pinecone_id

def main(data=None):
    print("30")
    try: 
        load_dotenv()

        api_key = os.getenv("MOCHA_PINECONE_API_KEY")
        environment = os.getenv("MOCHA_PINECONE_API_ENV")
        index_name = os.getenv("MOCHA_PINECONE_API_INDEX")

        Id = data["companyId"]
        company_name = data["company"].replace(' ', '_')
        reference_type = "Month"

        #######going to need to rewrite this to take in a dictionary of platforms and then iterate through each platform 7 times
        platform = "Facebook"

        company = get_company_profile(api_key, environment, index_name, Id)
        profile = build_company_profile(company)
        client_sample = get_client_sample(api_key, environment, index_name, Id)
        calendar_id = get_calendar_id(api_key, environment, index_name, Id)


        # Set the number of loop iterations
        # post_ids = {}
        num_iterations = 30
        times_through = 0

        # Start of a loop. Loop num_iterations times to create num_iterations days of content.
        for i in range(num_iterations):
            current_day = get_current_day(api_key, environment, index_name, calendar_id)
            idea = get_which_day(api_key, environment, index_name, Id, reference_type)
            post = create_day_post(company_name, current_day, profile, client_sample, calendar_id, Id, idea, platform)

            attempt = 0
            while attempt < 3:
                if not validate_summary(post):
                    # print("Invalid summary format! Rewriting...")
                    post = rewrite_summary(post)

                    # Validate the format of the new summary
                    if not validate_summary(post):
                        print("Invalid summary format after rewrite! Aborting...")
                        attempt += 1
                    else:
                        break
                else:
                    break

            if attempt == 3:
                print("Failed after 3 attempts. Aborting...")
                error = "30 Days failed to format correctly"
                failed(data, error)
            
            refinedPost = response_to_dict(post)
            pinecone_id = upsert_post(api_key, environment, index_name, refinedPost, Id)
            update_current_day(api_key, index_name, environment, current_day, Id)
            # ayshare_id = schedule_post(pinecone_id, refinedPost, times_through)
            # post_ids[f"post_{i+1}"] = ayshare_id
            # post_ids[f"post_{i+1}"] = pinecone_id
            times_through += 1


        newData = {
            "type": "Day",
            "companyId": data["companyId"],
            "company": company_name,
            "notes": "Placeholder",
            "isApproved": "false",
            "posts": calendar_id
        }

        # print(newData)
        print("Complete")
        create_process(newData)
    except Exception as e:
        print(f"Exception occurred: {e}")
        failed(data, str(e))
    
if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
    else:
        data = None
    main(data)