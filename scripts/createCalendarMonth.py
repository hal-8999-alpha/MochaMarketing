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


# def write_summary_to_file(summary, file_name):
#     with open(file_name, 'w') as file:
#         file.write(summary)
#     print(f"Summary written to {file_name}")


def failed(data, notes):
    Id = data.get("companyId")
    today = date.today()
    formatted_date = today.strftime('%Y-%m-%d')
    complete = "false"
    title = "Month Failed " + Id

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
    expected_headlines = ["Active", "Created", "Approved",
                          "Company", "Id", "Month", "Current Day", "Type"]
    expected_headlines.extend(["Day " + str(i) for i in range(1, 31)])

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
                    {"role": "system", "content": "You are given a company summary that needs to be rewritten in the correct format. The correct format contains exactly 38 headlines. The headlines are named Active, Created, Approved, Company, Id, Month, Current Day, Type and then 30 days starting with Day 1. There are no duplicate headlines. Each headline is followed by a colon and its corresponding content."},
                    {"role": "user", "content": f"""Please rewrite the following summary in the correct format and use the examples to help guide you. There will be exactly 38 headlines and no duplicates: {summary} EXAMPLE:

                        EXAMPLE: 

                        Active: Yes
                        Created: May 14
                        Approved: No
                        Company: FixedTest583038
                        Id: FixedTest583038
                        Company: Fixed Test
                        Month: May
                        Current Day: Day 1
                        Type: Month
                        Day 1: Introduce our coffee of the month with a creative and visually appealing post
                        Day 2: Showcase customers enjoying our coffee & tag them in the post
                        Day 3: Share a video tutorial on how to create coffee art
                        Day 4: Motivational Monday - Post an inspirational quote with our coffee in the background
                        Day 5: Share the history and origin of a popular coffee bean
                        Day 6: Highlight a positive customer review with an image of our coffee
                        Day 7: Host a live Q&A session with our baristas about brewing techniques
                        Day 8: Share a funny coffee meme or joke
                        Day 9: Post a poll to gather customer feedback on favorite roasts
                        Day 10: Freebie Friday - Offer a downloadable coffee recipe card
                        Day 11: Share a photo of a local event our coffee brand supported
                        Day 12: Announce weekly promotions and discounts
                        Day 13: Introduce a limited edition coffee flavor
                        Day 14: Share a unique coffee pairing idea with food
                        Day 15: Tease a new product launch with a behind-the-scenes photo
                        Day 16: Create a fun coffee-themed music playlist
                        Day 17: Recognize and celebrate National Coffee Day
                        Day 18: Showcase a DIY coffee scrub recipe
                        Day 19: Host a giveaway contest for a coffee gift set
                        Day 20: Share health benefits of coffee
                        Day 21: Post a video testimonial from a loyal customer
                        Day 22: Collaborate with a local bakery for a special promotion
                        Day 23: Share an infographic of popular coffee brewing methods
                        Day 24: Feature an employee's favorite coffee and why they love it
                        Day 25: Share discount code for online store purchases
                        Day 26: Post a guide to storing and keeping coffee fresh
                        Day 27: Highlight our sustainable and eco-friendly practices
                        Day 28: Share a creative coffee cocktail recipe
                        Day 29: Host a live tour of our roasting facility
                        Day 30: Recap the month's activities and thank our customers for their support"""},
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


def get_which_month(api_key, environment, index_name, Id):

    pinecone.init(api_key=api_key, environment=environment)

    # Connect to the index
    index = pinecone.Index(index_name=index_name)

    # Define the query vector (you may need to adjust the dimension and values)
    query_vector = [0] * 1536

    query_result = index.query(
        vector=query_vector,
        filter={'$and': [
            {'Id': {'$eq': Id}},
            {'Type': {'$eq': 'Quarter'}},
            {'Active': {'$eq': 'Yes'}},
            # {'Approved': {'$eq': 'Yes'}}
        ]},
        top_k=100,
        include_metadata=True
    )

    # print(query_result)

    if query_result and query_result["matches"][0]["metadata"]["Type"] == "Quarter":
        # Check if Active and Approved are "Yes"
        if query_result["matches"][0]["metadata"]["Active"] == "Yes":
            # Extract the current quarter key and value
            current_month_key = query_result["matches"][0]['metadata']['Current Month']
            current_month_value = query_result["matches"][0]['metadata'][current_month_key]

            # print(current_quarter_value)
            return current_month_value
        # else:
        #     print("The record is not active and/or approved")
    else:
        print("No matching data found")

def create_month_calendar(month, profile, Id, company_name):
    # print("Generating Calendar For the Month")
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    from datetime import datetime

    # Get the current month as a string
    month = datetime.now().strftime('%B')
    created = datetime.now().strftime('%B %d')

    MAX_RETRIES = 5
    for attempt in range(MAX_RETRIES):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are an expert in social media marketing planning for consumer facing coffee brands."},
                    {"role": "user", "content": f"""Design a one month marketing calendar filled with 30 ideas, one for each day. The calendar should be formatted exactly as follows with 38 headlines. Use the EXAMPLE for formatting. There should only be 38 lines (use a colon and space after each headline): 

            Active: Yes
            Created: {created}
            Approved: No
            Company: {company_name}
            Id: {Id}
            Type: Month
            Current Day: Day 1
            Month: {month}
            Day 1: [Idea related to the COMPANY PROFILE]
            Day 2: [Idea related to the COMPANY PROFILE]
            Day 3: [Idea related to the COMPANY PROFILE]
            ...
            Day 30: [Idea related to the COMPANY PROFILE]

        The Active, Created, Approved, Company, Id, Type, Current Day, and Month fields are ABSOLUTE and should be filled exactly as specified. The Day 1 to Day 30 fields are CREATIVE and should be filled based on your expertise and the provided COMPANY PROFILE. Each day's idea should be related to platforms listed in the COMPANY PROFILE. 

        COMPANY PROFILE: {profile}
        
        EXAMPLE: 
        Active: Yes
        Created: May 14
        Approved: No
        Company: Fixed Test
        Id: FixedTest583038
        Month: May
        Current Day: Day 1
        Type: Month
        Day 1: Introduce our coffee of the month with a creative and visually appealing post
        Day 2: Showcase customers enjoying our coffee & tag them in the post
        Day 3: Share a video tutorial on how to create coffee art
        Day 4: Motivational Monday - Post an inspirational quote with our coffee in the background
        Day 5: Share the history and origin of a popular coffee bean
        Day 6: Highlight a positive customer review with an image of our coffee
        Day 7: Host a live Q&A session with our baristas about brewing techniques
        Day 8: Share a funny coffee meme or joke
        Day 9: Post a poll to gather customer feedback on favorite roasts
        Day 10: Freebie Friday - Offer a downloadable coffee recipe card
        Day 11: Share a photo of a local event our coffee brand supported
        Day 12: Announce weekly promotions and discounts
        Day 13: Introduce a limited edition coffee flavor
        Day 14: Share a unique coffee pairing idea with food
        Day 15: Tease a new product launch with a behind-the-scenes photo
        Day 16: Create a fun coffee-themed music playlist
        Day 17: Recognize and celebrate National Coffee Day
        Day 18: Showcase a DIY coffee scrub recipe
        Day 19: Host a giveaway contest for a coffee gift set
        Day 20: Share health benefits of coffee
        Day 21: Post a video testimonial from a loyal customer
        Day 22: Collaborate with a local bakery for a special promotion
        Day 23: Share an infographic of popular coffee brewing methods
        Day 24: Feature an employee's favorite coffee and why they love it
        Day 25: Share discount code for online store purchases
        Day 26: Post a guide to storing and keeping coffee fresh
        Day 27: Highlight our sustainable and eco-friendly practices
        Day 28: Share a creative coffee cocktail recipe
        Day 29: Host a live tour of our roasting facility
        Day 30: Recap the month's activities and thank our customers for their support"""},
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

    return profile

def response_to_dict(response):
    # print("Coming into response to dict")
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

    # print("Response To Dict Result")
    # print(result)

    return result


def upsert_month_calendar(api_key, environment, index_name, plan, Id):
    import time

    # Set the OpenAI API key
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Concatenate all the key-value pairs into a single string
    full_text = " ".join(f"{key}: {value}" for key,
                         value in plan.items() if key != "Id")

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
        'id': Id + '_month_' + random_number,
        'values': embedded_text['data'][0]['embedding'],
        'metadata': plan
    }

    # Call index.upsert() with the single embedding
    index.upsert([embedding])

    # print("Success uploading embeddings to Pinecone.")
    # print("\n")

def update_current_month(api_key, index_name, environment, Id):
    #DO NOT delete. For some reason this is needed to override the global
    import datetime 
    # Initialize the Pinecone instance
    pinecone.init(api_key=api_key, environment=environment)


    index = pinecone.Index(index_name)
    query_vector = [0] * 1536  

    query_result = index.query(
        vector=query_vector,
        filter={'$and': [
            {'Type': {'$eq': "Quarter"}},
            {'Id': {'$eq': Id}},
            {'Active': {'$eq': "Yes"}}
        ]},
        top_k=1,
        include_metadata=True
    )

    # Extract the calendar ID
    calendarId = query_result["matches"][0]["id"]

    # Get the metadata
    metadata = query_result["matches"][0]["metadata"]

    # Define keys that are not months
    non_month_keys = ['Active', 'Approved', 'Company', 'Current Month', 'Id', 'Type']

    # Get the month keys by excluding the non-month keys from the metadata keys
    month_keys = [key for key in metadata.keys() if key not in non_month_keys]

    # Sort months in order
    month_keys.sort(key = lambda month: datetime.datetime.strptime(month, "%B")) 
    # print(month_keys)

    # Get the current month's position in the sorted list
    current_month_position = month_keys.index(metadata['Current Month'])
    # print(month_keys.index(metadata['Current Month']))

    # Check if the current month is the last month in the sorted list
    if current_month_position == len(month_keys) - 1:
        # Update the metadata and set Active to "No"
        # print("it would update to end")
        index.update(id=calendarId, set_metadata={"Current Month": month_keys[current_month_position], "Active": "No"})
        today = datetime.date.today() + datetime.timedelta(days=5)
        formatted_date = today.strftime('%Y-%m-%d')

        # Create the follow-up
        complete = "false"
        title = "Generate Quarter " + Id
        notes = Id
        
        newData = {
        "lead": title,
        "date": formatted_date, 
        "complete": complete,
        "notes": notes
        }

        create_follow_up(newData)
    else:
        # Get the next month from the sorted list
        updated_month = month_keys[current_month_position + 1]

        # Update the metadata
        index.update(id=calendarId, set_metadata={"Current Month": updated_month})
        
    
    # print("Updated")


def main(data=None):
    print("Month")
    try:
        load_dotenv()

        api_key = os.getenv("MOCHA_PINECONE_API_KEY")
        environment = os.getenv("MOCHA_PINECONE_API_ENV")
        index_name = os.getenv("MOCHA_PINECONE_API_INDEX")

        Id = data["companyId"]
        company_name = data["company"].replace(' ', '_')
        reference_type = "Quarter"

        company = get_company_profile(api_key, environment, index_name, Id)
        profile = build_company_profile(company)
        month = get_which_month(api_key, environment, index_name, Id)
        month_calendar = create_month_calendar(month, profile, Id, company_name)
        file_name = f"month_calendar_first_attempt_{Id}.txt"
        # write_summary_to_file(month_calendar, file_name)

        attempt = 0
        while attempt < 3:
            if not validate_summary(month_calendar):
                print("Invalid summary format! Rewriting...")
                month_calendar = rewrite_summary(month_calendar)
                file_name = f"rewritten_month_summary_{Id}.txt"
                # write_summary_to_file(month_calendar, file_name)

                # Validate the format of the new summary
                if not validate_summary(month_calendar):
                    print("Invalid summary format after rewrite! Aborting...")
                    attempt += 1
                else:
                    break
            else:
                break

        if attempt == 3:
            print("Failed after 3 attempts. Aborting...")
            return

        plan = response_to_dict(month_calendar)

        upsert_month_calendar(api_key, environment, index_name, plan, Id)
        update_current_month(api_key, index_name, environment, Id)

        newData = {
            "type": "Month",
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
