import requests

# Read in local private.key files - also can read from a DB
with open('.private.key') as f:
    profileKey = f.read()

payload = {'domain': 'ACME', 
        'privateKey': profileKey,
        'profileKey': 'PROFILE_KEY' }
headers = {'Content-Type': 'application/json', 
        'Authorization': 'Bearer API_KEY'}

r = requests.post('https://app.ayrshare.com/api/profiles/generateJWT', 
    json=payload, 
    headers=headers)
    
# print(r.json())