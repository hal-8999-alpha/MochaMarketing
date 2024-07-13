import pinecone
from dotenv import load_dotenv
import os
import sys
import json

def get_calendar(api_key, environment, index_name, Id, Type, CalendarId=None):

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
            # {'Calendar Id': {'$eq': CalendarId}},
            # {'Active': {'$eq': 'Yes'}},
            # {'Approved': {'$eq': 'Yes'}}
        ]},
        top_k=100,
        include_metadata=True
    )

    # Convert the query_result to a dictionary format
    query_result_dict = {
        "namespace": query_result.namespace,
        "matches": [
            {
                "id": match.id,
                "score": match.score,
                "values": match.values,
                "metadata": match.metadata
            }
            for match in query_result.matches
        ],
    }

    # Convert the query_result_dict to a JSON format
    # json_data = json.dumps(query_result_dict)

    print(query_result)



if __name__ == "__main__":
    # Pass In a business Id
    load_dotenv()

    api_key = os.getenv("MOCHA_PINECONE_API_KEY")
    environment = os.getenv("MOCHA_PINECONE_API_ENV")
    index_name = os.getenv("MOCHA_PINECONE_API_INDEX")

    Id = "MooseCoffeeCo640656"
    # CalendarId = "LakaJava304133_month_392389"
    Type = "Day"
    get_calendar(api_key, environment, index_name, Id, Type)


