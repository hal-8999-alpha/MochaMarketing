import time
import pinecone
import openai
from dotenv import load_dotenv
import os
import random

def create_embedding(content):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # print("Starting Embeddings...")
    while True:
        try:
            embedded_text = openai.Embedding.create(
                input=content,
                model="text-embedding-ada-002"
            )
            break
        except openai.error.RateLimitError as e:
            print(e)
            print("Waiting before retrying...")
            time.sleep(5)

    # print("Embeddings Complete!")
    return embedded_text['data'][0]['embedding']

def upsert_content_to_pinecone(content, id):
    load_dotenv()

    index_name = os.getenv("MOCHA_PINECONE_API_INDEX")
    PINECONE_API_KEY = os.getenv("MOCHA_PINECONE_API_KEY")
    PINECONE_API_ENV = os.getenv("MOCHA_PINECONE_API_ENV")

    random_number = str(random.randint(100000, 999999))
    pinecone_id = f"{id}_sample_{random_number}"

    embedding = create_embedding(content)

    metadata = {
        'Id': id,
        'Type': 'Sample',
        'Content': content,
    }

    pinecone_entry = {
        'id': pinecone_id,
        'values': embedding,
        'metadata': metadata
    }

    # print("Uploading to Pinecone...")

    pinecone.init(
        api_key=PINECONE_API_KEY,
        environment=PINECONE_API_ENV
    )

    index = pinecone.Index(index_name)
    index.upsert([pinecone_entry])

    # print("Success uploading content to Pinecone.")
    # print("\n")
    return pinecone_id
