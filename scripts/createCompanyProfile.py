#Takes in a text file of unstructured data, summarizes and formats then uploads to pinecone

import time
import pinecone
import openai
from dotenv import load_dotenv
import os
from datetime import datetime, date
import random
import re
from urllib.parse import urlparse
from controller import create_process, create_follow_up
import chardet
import sys
import json


def read_unstructured_data(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    detected_encoding = chardet.detect(raw_data)['encoding']
    return raw_data.decode(detected_encoding)

def failed(data, notes):
    Id = data.get("companyId")
    today = date.today()
    formatted_date = today.strftime('%Y-%m-%d')
    complete = "false"
    title = "Profile Failed " + Id

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
    expected_headlines = ["Active", "Company", "Competitive", "Id", "Mission", "Platforms", "Promotions", "Services", "Target", "Type", "Values"]

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
                    {"role": "system", "content": "You are given a company summary that needs to be rewritten in the correct format. The correct format contains 11 headlines named Active, Company, Competitive, Id, Mission, Platforms, Promotions, Services, Target, Type, and Values. Each headline is followed by a colon and its corresponding content."},
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

def generate_summary(unstructured_data, company_id, company_name):
    # print("Generating Company Profile")
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    MAX_RETRIES = 5
    for attempt in range(MAX_RETRIES):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are an expert at summarizing a company's unstructured data into a concise profile."},
                    {"role": "user", "content": f"""Create a company profile summary using the following format (use a colon and space after each headline):

            Id: {company_id}
            Type: Profile
            Active: Yes
            Company: {company_name}
            Platforms: Facebook
            Promotions: None
            Competitive: [Your analysis of the company's competitive advantage.]
            Mission: [Your interpretation of the company's mission.]
            Services: [Your summary of the services the company offers.]
            Target: [Your assessment of the company's target market.]
            Values: [Your understanding of the company's core values.]

        The Id, Type, Active, Company, Platforms, and Promotions fields are ABSOLUTE and should be filled exactly as specified. The Competitive, Mission, Services, Target, and Values fields are CREATIVE and should be filled based on your analysis and the provided UNSTRUCTURED DATA. 

        UNSTRUCTURED DATA: {unstructured_data}
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


def parse_summary(summary):
    # Parse the summary into chunks based on the headline of each paragraph
    # print("Parsing Summary")
    chunks = []
    pattern = r"([A-Za-z\s]+): (.+?(?=\n|$))"
    matches = re.findall(pattern, summary, re.MULTILINE)

    for match in matches:
        headline, content = match
        chunks.append({'headline': headline.strip(), 'content': content.strip()})
    # print(chunks)
    return chunks

# def write_summary_to_file(summary, file_name):
#     with open(file_name, 'w') as file:
#         file.write(summary)
#     print(f"Summary written to {file_name}")

def upsert_summary(summary, chunks, company_name, chosen_database):
    load_dotenv()

    openai.api_key = os.getenv("OPENAI_API_KEY")

    index_name = chosen_database["PINECONE_API_INDEX"]
    PINECONE_API_KEY = chosen_database["PINECONE_API_KEY"]
    PINECONE_API_ENV = chosen_database["PINECONE_API_ENV"]

    # Create a single Embedding for the whole summary
    # print("Starting Embeddings...")
    
    while True:
        try:
            embeddedText = openai.Embedding.create(
                input=summary,
                model="text-embedding-ada-002"
            )
            break
        except openai.error.RateLimitError as e:
            print(e)
            print("Waiting before retrying...")
            time.sleep(5)

    # print("Embedding Complete!")

    # Create metadata using the headlines of the chunks
    metadata = {chunk['headline']: chunk['content'] for chunk in chunks}

    random_number = str(random.randint(100000, 999999))
    company_name_no_spaces = company_name.replace(" ", "")
    new_company_id = company_name_no_spaces + "_profile_" + str(random_number)

    # Create a single entry for the company
    embedding = {
        'id': new_company_id,
        'values': embeddedText['data'][0]['embedding'],
        'metadata': metadata
    }

    # print("Uploading to Pinecone...")

    pinecone.init(
        api_key=PINECONE_API_KEY,
        environment=PINECONE_API_ENV
    )

    index = pinecone.Index(index_name)
    index.upsert([embedding])

    # print("Success uploading embeddings to Pinecone.")
    # print("\n")

# Add data parameter to the main function
def main(data=None):
    # Read unstructured data from a text file
    print("Profile")
    try:
        # print(data["companyId"])
    
        parsed_url = urlparse(data['url'])
        domain = f"{parsed_url.netloc}"
        file_path = f"{domain}.txt"
        Id = data.get("companyId")
        email = data.get("email")

        unstructured_data = read_unstructured_data(file_path)

        company_name = data["company"].replace(' ', '_')

        # print(company_name)
        # Generate summary using OpenAI
        summary = generate_summary(unstructured_data, Id, company_name)

        # file_name = "before_profile_summary.txt"
        # write_summary_to_file(summary, file_name)

        # Validate the format of the summary
        if not validate_summary(summary):
            # print("Invalid summary format! Rewriting...")
            summary = rewrite_summary(summary)
            # file_name = "rewritten_profile_summary.txt"
            # write_summary_to_file(summary, file_name)
            # Validate the format of the new summary
            if not validate_summary(summary):
                print("Invalid summary format after rewrite! Aborting...")
                return

        # Parse the summary into chunks
        chunks = parse_summary(summary)

        # Load environment variables from the .env file
        load_dotenv()

        # Define the chosen Pinecone database using environment variables
        chosen_database = {
            "PINECONE_API_INDEX": os.getenv("MOCHA_PINECONE_API_INDEX"),
            "PINECONE_API_KEY": os.getenv("MOCHA_PINECONE_API_KEY"),
            "PINECONE_API_ENV": os.getenv("MOCHA_PINECONE_API_ENV")
        }

        # Upsert the summary to Pinecone
        upsert_summary(summary, chunks, company_name, chosen_database)

        newData = {
        "type": "Profile",
        "companyId": data["companyId"],
        "company": company_name,
        "notes": "Placeholder",
        "isApproved": "false",
        "email": email
        }

        # print(newData)

        create_process(newData)
        print("Complete")
    except Exception as e:
        failed(data, str(e))

# Call the main function with the data object
if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
    else:
        data = None
    main(data)