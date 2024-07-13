import requests

payload = {'title': 'ACME Profile'}
headers = {'Content-Type': 'application/json', 
        'Authorization': 'Bearer API_KEY'}

r = requests.post('https://app.ayrshare.com/api/profiles/profile', 
    json=payload, 
    headers=headers)
    
# print(r.json())