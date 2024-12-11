from ruamel.yaml import YAML
import json

# Initialize YAML parser
yaml = YAML()
yaml.preserve_quotes = True

# Load activities.yml
with open('activities.yml', 'r') as yml_file:
    activities = yaml.load(yml_file)

# Load gh-data-summary.json
with open('gh-data-summary.json', 'r') as json_file:
    gh_data_summary = json.load(json_file)

# Create a dictionary with 'issue' as key for easy lookup in gh-data-summary.json
output_dict = {item['issue']: item for item in gh_data_summary}

def merge(dict1, dict2):
    """
    Merges data from dict1 into dict2. Keys in dict1 take precedence if not None.
    Strips trailing newline from string values.
    """
    for key, value in dict1.items():
        if value is not None:
            if isinstance(value, str):
                dict2[key] = value.rstrip("\n")  # Strip trailing newlines
            else:
                dict2[key] = value
    dict2.pop('issue', None)  # Remove the 'issue' key after merging

# Merge data
for activity_title, activity_data in activities.items():
    if 'issue' in activity_data:
        issue_number = activity_data['issue']
        if issue_number in output_dict:
            merge(activity_data, output_dict[issue_number])

# Output as JSON
with open("merged-data.json", "w") as f:
    json.dump(output_dict, f, indent=2, separators=(",", ": "))
    f.write("\n")
