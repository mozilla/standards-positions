import yaml
import json

# Load activities.yml
with open('activities.yml', 'r') as yml_file:
    activities = yaml.safe_load(yml_file)

# Load gh-data-summary.json
with open('gh-data-summary.json', 'r') as json_file:
    gh_data_summary = json.load(json_file)

# Create a dictionary with 'title' as key for easy lookup
gh_data_dict = {item['title']: item for item in gh_data_summary}

# Function to compare two dictionaries and return differences
def compare_dicts(dict1, dict2):
    differences = {}
    for key in dict1:
        if key in dict2:
            if dict1[key] != dict2[key]:
                differences[key] = {'activities.yml': dict1[key], 'gh-data-summary.json': dict2[key]}
    return differences

# Compare the files and find differences
differences = {}
for activity_title, activity_data in activities.items():
    if activity_title in gh_data_dict:
        diff = compare_dicts(activity_data, gh_data_dict[activity_title])
        if diff:
            differences[activity_title] = diff

# Output the differences as JSON
print(json.dumps(differences, indent=4))
