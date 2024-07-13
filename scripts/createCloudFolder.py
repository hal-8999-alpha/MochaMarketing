import requests
import os

def create_cloudinary_folder(folder_name):
    cloud = os.getenv("CLOUDINARY_CLOUD_NAME")
    secret = os.getenv("CLOUDINARY_SECRET")
    cloudinary_api_key = os.getenv("CLOUDINARY_API_KEY")

    subfolders = ["content", "profile"]

    for subfolder in subfolders:
        url = f"https://{cloudinary_api_key}:{secret}@api.cloudinary.com/v1_1/{cloud}/folders/{folder_name}/{subfolder}"
        
        try:
            response = requests.post(url)
            response.raise_for_status()
            # print(f"Created {folder_name}/{subfolder} Folder Successfully")
        except requests.exceptions.RequestException as err:
            print(f"Error creating {folder_name}/{subfolder} folder:", err)
            return f"Error creating {folder_name}/{subfolder} folder for your company"

if __name__ == "__main__":
    folder_name = input("Enter folder name: ")
    
    create_cloudinary_folder(folder_name)
