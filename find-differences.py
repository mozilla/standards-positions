import yaml
import json

# Load activities.yml
with open('activities.yml', 'r') as yml_file:
    activities = yaml.safe_load(yml_file)

# Load gh-data-summary.json
with open('gh-data-summary.json', 'r') as json_file:
    gh_data_summary = json.load(json_file)

# Create a dictionary with 'issue' as key for easy lookup in gh-data-summary.json
gh_data_dict = {item['issue']: item for item in gh_data_summary}

# Function to compare the 'position' key between two dictionaries
def compare_position(dict1, dict2):
    differences = {}
    if 'position' in dict1 and 'position' in dict2:
        if dict1['position'] != dict2['position']:
            differences['position'] = {'activities.yml': dict1['position'], 'gh-data-summary.json': dict2['position']}
    return differences

# Compare the files and find differences in 'position' using 'issue' as the key
differences = {}
for activity_title, activity_data in activities.items():
    if 'issue' in activity_data:
        issue_number = activity_data['issue']
        if issue_number in gh_data_dict:
            diff = compare_position(activity_data, gh_data_dict[issue_number])
            if diff:
                differences[issue_number] = diff

# Output the differences as JSON
print(json.dumps(differences, indent=4))
