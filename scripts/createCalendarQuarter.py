
import pinecone
from dotenv import load_dotenv
import os
import openai
import sys
import json
from controller import create_process, create_follow_up
import time
from datetime import date, datetime, timedelta
import re
import calendar

# def write_summary_to_file(summary, file_name):
#     with open(file_name, 'w') as file:
#         file.write(summary)
#     print(f"Summary written to {file_name}")

def failed(data, notes):
    Id = data.get("companyId")
    today = date.today()
    formatted_date = today.strftime('%Y-%m-%d')
    complete = "false"
    title = "Quarter Failed " + Id

    newData = {
        "lead": title,
        "date": formatted_date, 
        "complete": complete,
        "notes": Id
    }

    create_follow_up(newData)

def validate_summary(summary):
    """Validate the format of the summary."""
    # Get the current month
    now = datetime.now()
    current_month = calendar.month_name[now.month]
    next_month = calendar.month_name[now.month % 12 + 1]  # Use modulus to cycle back to January after December
    month_after_next = calendar.month_name[now.month % 12 + 2]  # Use modulus to cycle back to January after December

    # Define the expected headlines
    expected_headlines = ["Active", "Approved", "Company", "Id", "Current Month", "Type", current_month, next_month, month_after_next]

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

    now = datetime.now()
    current_month = calendar.month_name[now.month]

    MAX_RETRIES = 5
    for attempt in range(MAX_RETRIES):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are given a company summary that needs to be rewritten in the correct format. The correct format contains 9 headlines named Active, Approved, Company, Id, Current Month, Type and then three months starting from {current_month} including {current_month}. Each headline is followed by a colon and its corresponding content."},
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

def get_which_quarter(api_key, environment, index_name, Id, Type):

    pinecone.init(api_key=api_key, environment=environment)

    # Connect to the index
    index = pinecone.Index(index_name=index_name)

    # Define the query vector (you may need to adjust the dimension and values)
    query_vector = [0] * 1536  

    query_result = index.query(
        vector=query_vector,
        filter={'$and': [
            {'Id': {'$eq': Id}},
            {'Type': {'$eq': Type}},
            {'Active': {'$eq': 'Yes'}},
        ]},
        top_k=100,
        include_metadata=True
    )

    # print(query_result)

    if query_result and query_result["matches"][0]["metadata"]['Type'] == Type:
        # Check if Active
        if query_result["matches"][0]['metadata']['Active'] == "Yes":
            # Extract the current quarter key and value
            current_quarter_key = query_result["matches"][0]['metadata']['Quarter']
            current_quarter_value = query_result["matches"][0]['metadata'][current_quarter_key]

            # print(current_quarter_value)
            return current_quarter_value
        else:
            print("The record is not active and/or approved")
    else:
        print("No matching data found")

    # print(query_result["matches"][0]["metadata"])

# def create_quarterly_calendar(current_quarter_value, company_profile, Id, company_name):
#     # print(current_quarter_value)
#     print("Generating Calendar For the Quarter")
#     load_dotenv()
#     openai.api_key = os.getenv("OPENAI_API_KEY")

#     # current_date = datetime.now().strftime("%m/%d/%Y")

#     from datetime import datetime

#     # Get the current month as a string
#     month = datetime.now().strftime('%B')

#     MAX_RETRIES = 5
#     for attempt in range(MAX_RETRIES):
#         try:
#             response = openai.ChatCompletion.create(
#                 model="gpt-4",
#                 messages=[
#                     {"role": "system", "content": f"You are an expert in social media marketing planning for consumer facing coffee brands."},
#                     {"role": "user", "content": f"Design a three month marketing calendar starting from today's date with the following COMPANY PROFILE following the goals of THIS QUARTER and outputting with the EXAMPLE format. The goals should be easy for a social media manager to fullfil by themselves. There should be 9 headlines. The headlines are named Active, Approved, Company, Id, Current Month, Type and then three months starting from today's month. You will use a colon after every headline. 5 headlines are ABSOLUTE. Id, Active, Type, Approved and Current Month are ABSOLUTE. If they are ABSOLUTE then the value after the headline is exactly what comes after the equals sign. Id={Id}. Type =Quarter. Current Month ={month}. Approved =No. Active =Yes. Company should match the Company field from the COMPANY PROFILE. Use a colon after each Month. Everything else should be plain text. Have three points for each Month. End each point with a period. Only use platforms listed. COMPANY PROFILE: {company_profile} THIS QUARTER: {current_quarter_value} EXAMPLE: Id: Xyz309394 Company: Xyz Active: Yes Approved: No Type: Quarter Current Month: April April: sample text 1, sample text 2, sample text 3. May: sample text 1, sample text 2, sample text 3. June: sample text 1, sample text 2, sample text 3."},
#                 ]
#             )
#             return response['choices'][0]['message']['content']
#         except Exception as e:
#             if attempt < MAX_RETRIES - 1:  # i.e. not on last attempt
#                 print(f"Attempt {attempt+1} failed, retrying in 2 seconds.")
#                 time.sleep(2)  # wait for 2 seconds before retrying
#                 continue
#             else:
#                 print(f"Attempt {attempt+1} failed, giving up.")
#                 print(f"Error: {str(e)}")
#                 return None

def create_quarterly_calendar(quarter_goal, profile, Id, company_name):
    # print("Generating Calendar For the Quarter")
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    from datetime import datetime

    # Get the current month as a string
    month = datetime.now().strftime('%B')

    now = datetime.now()
    current_month = calendar.month_name[now.month]
    next_month = calendar.month_name[now.month % 12 + 1]  # Use modulus to cycle back to January after December
    month_after_next = calendar.month_name[now.month % 12 + 2] 

    MAX_RETRIES = 5
    for attempt in range(MAX_RETRIES):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are an expert in social media marketing planning for consumer facing coffee brands."},
                    {"role": "user", "content": f"""Design a quarterly marketing calendar starting from {current_month}, filled with goals for each month. The calendar should be formatted exactly as follows (use a colon and space after each headline): 

            Id: {Id}
            Type: Quarter
            Active: Yes
            Approved: No
            Company: {company_name}
            Current Month: {month}
            {current_month}: [Three marketing goals related to the COMPANY PROFILE and THIS QUARTER GOAL. Each goal should end with a period]
            {next_month}: [Three marketing goals related to the COMPANY PROFILE and THIS QUARTER GOAL.  Each goal should end with a period]
            {month_after_next} [Three marketing goals related to the COMPANY PROFILE and THIS QUARTER GOAL. Each goal should end with a period]

        The Id, Type, Active, Approved, Company, and Current Month fields are ABSOLUTE and should be filled exactly as specified. {current_month}, {next_month}, and {month_after_next} fields are CREATIVE and should be filled based on your expertise and the provided COMPANY PROFILE. Each month's goals should be related to platforms listed in the COMPANY PROFILE. 

        COMPANY PROFILE: {profile}
        THIS QUARTER GOAL: {quarter_goal}
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
    # print("line 92")
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

def response_to_dict(response):
    # print(response)

    now = datetime.now()
    current_month = calendar.month_name[now.month]
    next_month = calendar.month_name[now.month % 12 + 1]  # Use modulus to cycle back to January after December
    month_after_next = calendar.month_name[now.month % 12 + 2] 

    lines = response.strip().split('\n')

    result = {}
    current_key = ""

    for line in lines:
        if not line.strip():
            continue
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            if key in [current_month, next_month, month_after_next]:
                if current_key != "":
                    result[current_key] = result[current_key].strip()
                current_key = key
                result[current_key] = value
            else:
                if key == "Company":
                    result[key] = ' '.join(value.split())
                else:
                    result[key] = value
        elif current_key in [current_month, next_month, month_after_next]:
            result[current_key] += " " + line.strip()

    if current_key in [current_month, next_month, month_after_next]:
        result[current_key] = result[current_key].strip()

    return result





def upsert_quarter_calendar(api_key, environment, index_name, plan, Id):
    import time
    
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
        'id': Id + '_quarter_'+ random_number,
        'values': embedded_text['data'][0]['embedding'],
        'metadata': plan
    }

    # Call index.upsert() with the single embedding
    index.upsert([embedding])

    # print("Success uploading embeddings to Pinecone.")
    # print("\n")

def update_current_quarter(api_key, index_name, environment, Id, data):
    
    pinecone.init(
        api_key=api_key,
        environment=environment
    )

    index = pinecone.Index(index_name)

    query_vector = [0] * 1536  

    query_result = index.query(
        vector=query_vector,
        filter={'$and': [
            {'Type': {'$eq': "Year"}},
            {'Id': {'$eq': Id}},
            {'Active': {'$eq': "Yes"}}
        ]},
        top_k=1,
        include_metadata=True
    )

    calendarId = query_result["matches"][0]["id"]
    current_quarter = query_result["matches"][0]["metadata"]["Quarter"]

    quarter_number = int(current_quarter.strip("Q")) + 1
    updated_quarter = f"Q{quarter_number}"

    if quarter_number == 5:
        index.update(id=calendarId, set_metadata={"Quarter": updated_quarter, "Active": "No"})
    # HERE we need to grab the next calendar content
    elif quarter_number == 4:
        index.update(id=calendarId, set_metadata={"Quarter": updated_quarter})
        Id = data.get("companyId")
        today = date.today() + timedelta(days=70)  # set date to 60 days from today
        formatted_date = today.strftime('%Y-%m-%d')
        complete = "false"
        title = "Generate Year " + Id
        notes = Id

        newData = {
        "lead": title,
        "date": formatted_date, 
        "complete": complete,
        "notes": notes
        }

        create_follow_up(newData)
    else:
        index.update(id=calendarId, set_metadata={"Quarter": updated_quarter})
    
    # print("Updated")

def main(data=None):
    print("Quarter")
    try:
        # Example usage:
        load_dotenv()

        api_key = os.getenv("MOCHA_PINECONE_API_KEY")
        environment = os.getenv("MOCHA_PINECONE_API_ENV")
        index_name = os.getenv("MOCHA_PINECONE_API_INDEX")

        Id = data["companyId"]
        company_name = data["company"].replace(' ', '_')
        reference_type = "Year"
        type = "Quarter"

        # print(company_name)
        # print(Id)

        company = get_company_profile(api_key, environment, index_name, Id)
        profile = build_company_profile(company)
        quarter = get_which_quarter(api_key, environment, index_name, Id, reference_type)
        quarter_calendar = create_quarterly_calendar(quarter, profile, Id, company_name)
        file_name = f"quarter_summary_first_attempt_{Id}.txt"
        # write_summary_to_file(quarter_calendar, file_name)

        attempt = 0
        while attempt < 3:
            if not validate_summary(quarter_calendar):
                print("Invalid summary format! Rewriting...")
                quarter_calendar = rewrite_summary(quarter_calendar)
                file_name = f"rewritten_quarter_summary_{Id}.txt"
                # write_summary_to_file(quarter_calendar, file_name)

                # Validate the format of the new summary
                if not validate_summary(quarter_calendar):
                    print("Invalid summary format after rewrite! Aborting...")
                    attempt += 1
                else:
                    break
            else:
                break

        if attempt == 3:
            print("Failed after 3 attempts. Aborting...")
            return

        plan = response_to_dict(quarter_calendar)
        upsert_quarter_calendar(api_key, environment, index_name, plan, Id)
        update_current_quarter(api_key, index_name, environment, Id, data)

        newData = {
        "type": "Quarter",
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



