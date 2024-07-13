import os
import pinecone
from dotenv import load_dotenv
import sys

def update(api_key, index_name, environment, value, vectorId, field):

    # print(field)
    # print(value)
    # print(vectorId)
    
    pinecone.init(
        api_key=api_key,
        environment=environment
    )

    index = pinecone.Index(index_name)
    # print(vectorId, {field: value})

    index.update(id=vectorId, set_metadata={field: value})
    print("Updated")
    return True


if __name__ == "__main__":
    load_dotenv()

    api_key = os.getenv("MOCHA_PINECONE_API_KEY")
    environment = os.getenv("MOCHA_PINECONE_API_ENV")
    index_name = os.getenv("MOCHA_PINECONE_API_INDEX")

    value = sys.argv[1]
    vectorId = sys.argv[2]
    field = sys.argv[3]

    update(api_key, index_name, environment, value, vectorId, field)
