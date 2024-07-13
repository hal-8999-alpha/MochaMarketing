import pinecone
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("MOCHA_PINECONE_API_KEY")
environment = os.getenv("MOCHA_PINECONE_API_ENV")
index_name = os.getenv("MOCHA_PINECONE_API_INDEX")

pinecone.init(api_key=api_key, environment=environment)

# Connect to the index
index = pinecone.Index(index_name=index_name)

# index.delete(
#     filter={
#         "Type": {"$eq": "Month"},
#     }
# )


index.delete(
    filter={
        "Type": { "$in": ["Year", "Day", "Profile", "'Profile'", "Month", "Quarter", "Sample"] }
    }
)

# index.delete(
#     filter={
#         "Type": { "$in": ["Year", "Day", "Month", "Quarter", "Sample"] }
#     }
# )

# index.delete(ids=["HopefulTest819392_quarter_767741"])
