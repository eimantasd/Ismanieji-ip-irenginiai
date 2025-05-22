import json

x = {
  "firstName": "Antanas",
  "lastName": "Antanaitis",
  "age": 25,
  "city": "Kaunas",
  "isStudent": True,
}

y = json.dumps(x)

print(y)