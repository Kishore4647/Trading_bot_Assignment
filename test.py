import requests

headers = {
    "X-MBX-APIKEY": 'JGqmvDdP1bdN3xLdFsuux9JI7kLgGIU3ACjvy8vb4bLT55atou5tODuOrtl5w05n'
}

r = requests.get(
    "https://testnet.binancefuture.com/fapi/v2/balance",
    headers=headers
)

print(r.text)