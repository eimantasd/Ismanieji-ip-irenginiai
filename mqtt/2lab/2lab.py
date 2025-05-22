import json

# Read the JSON files
with open('users1.json', 'r') as file1:
    users1_data = json.load(file1)

with open('users2.json', 'r') as file2:
    users2_data = json.load(file2)

# Extract the users dictionaries
users1 = users1_data['table']['users']
users2 = users2_data['table']['users']

# Merge users: add users from users2 that are not in users1
for user_id, user_info in users2.items():
    if user_id not in users1:
        users1[user_id] = user_info

# Create the output data structure
output_data = {
    'table': {
        'users': users1
    }
}

# Save the merged data to users.json
with open('users.json', 'w') as output_file:
    json.dump(output_data, output_file, indent=4)

print("Merged data saved to users.json")