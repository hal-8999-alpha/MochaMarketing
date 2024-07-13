import cloudinary
from cloudinary.utils import api_sign_request
import os
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
  cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
  api_key=os.getenv("CLOUDINARY_API_KEY"),
  api_secret=os.getenv("CLOUDINARY_SECRET")
)

def generate_cloudinary_signature(timestamp):
    # Create a string to sign with the timestamp parameter
    string_to_sign = f"timestamp={timestamp}"
    # Generate the signature using the Cloudinary API Secret
    signature = api_sign_request(string_to_sign, cloudinary.config().api_secret)
    return signature
