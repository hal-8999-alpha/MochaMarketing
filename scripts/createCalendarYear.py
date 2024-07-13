import os
import pinecone
import openai
from dotenv import load_dotenv
import time
import sys
import json
import re
from controller import create_process, create_follow_up
from datetime import date

# def write_summary_to_file(summary, file_name):
#     with open(file_name, 'w') as file:
#         file.write(summary)
#     print(f"Summary written to {file_name}")

def failed(data, notes):
    Id = data.get("companyId")
    today = date.today()
    formatted_date = today.strftime('%Y-%m-%d')
    complete = "false"
    title = "Year Failed " + Id

    newData = {
        "lead": title,
        "date": formatted_date, 
        "complete": complete,
        "notes": Id
    }

    create_follow_up(newData)

def validate_summary(summary):
    """Validate the format of the summary."""
    # Define the expected headlines
    expected_headlines = ["Active", "Approved", "Company", "Id", "Quarter", "Type", "Q1", "Q2", "Q3", "Q4"]

    # Check each headline
    for headline in expected_headlines:
        # Check if the headline is in the summary
        if headline not in summary:
            print(f"Missing headline: {headline}")
            return False

        # Check if the headline is followed by a colon
        if not re.search(f"{headline}: ", summary):
            print(f"Missing colon after headline: {headline}")
            return False

    # Check if there are any other headlines
    for line in summary.split('\n'):
        headline = line.split(': ')[0]
        if headline not in expected_headlines:
            print(f"Unexpected headline: {headline}")
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
                    {"role": "system", "content": "You are given a company summary that needs to be rewritten in the correct format. The correct format contains 10 headlines named Active, Approved, Company, Id, Quarter, Type, Q1, Q2, Q3 and Q4. Each headline is followed by a colon and its corresponding content."},
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
    # profile_type = metadata['Type']
    services = metadata['Services']
    mission = metadata['Mission']
    competitive_advantage = metadata['Competitive']
    values = metadata['Values']
    target_market = metadata['Target']
    platforms = metadata['Platforms']
    # active = metadata['Active']

    profile = (
        f"Id: {id}\n"
        f"Company: {company}\n"
        # f"Type: {profile_type}\n"
        f"Services: {services}\n"
        f"Mission: {mission}\n"
        f"Competitive Advantage: {competitive_advantage}\n"
        f"Values: {values}\n"
        f"Target Market: {target_market}\n"
        f"Platforms: {platforms}\n"
        f"Promotions: \n"
        # f"Active: {active}"
    )

    # print(profile)
    return profile


def create_year_calendar(company_profile, company_id, company):
    # print("Generating Calendar For the Year")
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    MAX_RETRIES = 5
    for attempt in range(MAX_RETRIES):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are an expert in social media marketing planning for consumer facing coffee brands."},
                    {"role": "user", "content": f"""Starting from today's date, design a marketing goal calendar for a company. The calendar should be formatted exactly as follows (use a colon and space after each headline): 

            Id: {company_id}
            Type: Year
            Active: Yes
            Approved: No
            Quarter: Q1
            Company: {company}
            Q1: [Three marketing goals related to the COMPANY PROFILE. Each goal should end with a period]
            Q2: [Three marketing goals related to the COMPANY PROFILE. Each goal should end with a period]
            Q3: [Three marketing goals related to the COMPANY PROFILE. Each goal should end with a period]
            Q4: [Three marketing goals related to the COMPANY PROFILE. Each goal should end with a period]

        The Id, Type, Active, Approved, Quarter, and Company fields are ABSOLUTE and should be filled exactly as specified. The Q1, Q2, Q3, and Q4 fields are CREATIVE and should be filled based on your expertise and the provided COMPANY PROFILE. Each quarter's goals should be related to platforms listed in the COMPANY PROFILE. 

        COMPANY PROFILE: {company_profile}
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

def response_to_dict(response):
    # print(response)
    
    lines = response.strip().split('\n')

    result = {}
    current_key = ""

    for line in lines:
        if not line.strip():
            continue
        try:  # First try
            key, value = line.split(':', 1)
        except ValueError:  # Second try if the first fails
            if ':' in line:
                key, value = line.split(':', 1)
            else:
                continue  # If there is no ':' in line, skip it

        if key == "Company":
            result[key.strip()] = value.split()[0]
            pairs = value.split()[1:]
            for pair in pairs:
                if ':' in pair:
                    sub_key, sub_value = pair.split(':', 1)
                    result[sub_key.strip()] = sub_value.strip()
                    current_key = sub_key.strip()
                elif current_key:
                    result[current_key] += f" {pair.strip()}"
        else:
            result[key.strip()] = value.strip()

    for key, value in result.items():
        result[key] = value.strip()

    return result








def upsert_year_calendar(api_key, environment, index_name, plan, Id):
    # Set the OpenAI API key
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Concatenate all the key-value pairs into a single string
    full_text = " ".join(f"{key}: {value}" for key, value in plan.items() if key != "Id")

    # print("Starting Embeddings...")
    while True:
        try:
            embedded_text = openai.Embedding.create(
                input=full_text,
                model="text-embedding-ada-002"
            )
            break
        except openai.error.RateLimitError as e:
            print(e)
            print("Waiting before retrying...")
            time.sleep(5)

    # print("Embeddings Complete!")
    # print("Uploading to Pinecone...")

    pinecone.init(
        api_key=api_key,
        environment=environment
    )

    index = pinecone.Index(index_name)

    import random
    random_number = str(random.randint(100000, 999999))

    # Create a single embedding with metadata
    embedding = {
        'id': Id + '_year_'+ random_number,
        'values': embedded_text['data'][0]['embedding'],
        'metadata': plan
    }

    # Call index.upsert() with the single embedding
    index.upsert([embedding])

    # print("Success uploading embeddings to Pinecone.")
    # print("\n")

    # pinecone.deinit()

def main(data=None):
    print("Year")
    try:
        load_dotenv()

        api_key = os.getenv("MOCHA_PINECONE_API_KEY")
        environment = os.getenv("MOCHA_PINECONE_API_ENV")
        index_name = os.getenv("MOCHA_PINECONE_API_INDEX")

    
        Id = data["companyId"]
        Type = data["type"]
        company_name = data["company"].replace(' ', '_')

        # print(company_name)

        company = get_company_profile(api_key, environment, index_name, Id)
        profile = build_company_profile(company)
        year_calendar = create_year_calendar(profile, Id, company_name)
        file_name = f"year_calendar_{Id}_first_attempt.txt"
        # write_summary_to_file(year_calendar, file_name)

        attempt = 0
        while attempt < 3:
            if not validate_summary(year_calendar):
                print("Invalid summary format! Rewriting...")
                year_calendar = rewrite_summary(year_calendar)
                file_name = f"rewritten_year_summary_{Id}.txt"
                # write_summary_to_file(year_calendar, file_name)

                # Validate the format of the new summary
                if not validate_summary(year_calendar):
                    print("Invalid summary format after rewrite! Aborting...")
                    attempt += 1
                else:
                    break
            else:
                break

        if attempt == 3:
            print("Failed after 3 attempts. Aborting...")
            return

        plan = response_to_dict(year_calendar)
        upsert_year_calendar(api_key, environment, index_name, plan, Id)

        newData = {
        "type": "Year",
        "companyId": data["companyId"],
        "company": company_name,
        "notes": "Placeholder",
        "isApproved": "false"
        }

        # print(newData)
        print("Complete")
        create_process(newData)
    except Exception as e:
        failed(data, str(e))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
    else:
        data = None
    main(data)