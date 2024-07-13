import pinecone
from dotenv import load_dotenv
import os

def get_sample(api_key, environment, index_name, Id):
    
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
        top_k=10,
        include_metadata=True
    )

    sample = query_result["matches"][0]["metadata"]["Content"]

    # print(query_result)
    # print(sample)
    return sample

load_dotenv()

api_key = os.getenv("MOCHA_PINECONE_API_KEY")
environment = os.getenv("MOCHA_PINECONE_API_ENV")
index_name = os.getenv("MOCHA_PINECONE_API_INDEX")

#Pass In a business Id
Id = "LakaJava957193"
get_sample(api_key, environment, index_name, Id)