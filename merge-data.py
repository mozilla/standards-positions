import yaml
import json

# Load activities.yml
with open('activities.yml', 'r') as yml_file:
    activities = yaml.safe_load(yml_file)

# Load gh-data-summary.json
with open('gh-data-summary.json', 'r') as json_file:
    gh_data_summary = json.load(json_file)

# Create a dictionary with 'issue' as key for easy lookup in gh-data-summary.json
output_dict = {item['issue']: item for item in gh_data_summary}

def merge(dict1, dict2):
    for key in dict1.keys():
        if dict1[key]:
            dict2[key] = dict1[key]
    dict2.pop('issue', None)

for activity_title, activity_data in activities.items():
    if 'issue' in activity_data:
        issue_number = activity_data['issue']
        if issue_number in output_dict:
            merge(activity_data, output_dict[issue_number])

# Output as JSON
with open("merged-data.json", "w") as f:
    json.dump(output_dict, f, indent=2, separators=(",", ": "))
    f.write("\n")
