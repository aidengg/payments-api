import requests 

response = requests.get("https://api.frankfurter.app/latest?from=USD&to=KWD")

data = response.json()

print(data)