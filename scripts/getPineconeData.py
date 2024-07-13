import pinecone
from dotenv import load_dotenv
import os
import sys
import json

def get_pinecone_data(api_key, environment, index_name, Id, Type):

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

    return query_result_dict

if __name__ == '__main__':
    api_key, environment, index_name, Id, Type = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
    result = get_pinecone_data(api_key, environment, index_name, Id, Type)
    print(json.dumps(result))