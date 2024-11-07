import json
import yaml
import html

# Load the JSON data
with open('activities.json', 'r') as json_file:
    json_data = json.load(json_file)

# Convert to YAML format
yaml_data = {}

def fixupCaniuse(value):
    if value:
        if value.startswith("https://caniuse.com"):
            return value
        return "https://caniuse.com/" + value
    return value

for item in json_data:
    title = html.unescape(item['title'])
    yaml_data[title] = {
        'id': item['id'],
        'description': item['description'],  # html.unescape(item['description']),
        'rationale': item['mozPositionDetail'],  # html.unescape(item['mozPositionDetail']) if item['mozPositionDetail'] else None,
        # 'seealso': item['seealso'],
        'bug': item['mozBugUrl'],
        'position': item['mozPosition'],
        'issue': item['mozPositionIssue'],
        'venues': [ item['org'] ],
        'url': item['url'],
        'caniuse': fixupCaniuse(item['ciuName']),
        'mdn': item['mdnUrl'] if 'mdnUrl' in item else None,
    }

# Save as YAML
with open('activities.yml', 'w') as yaml_file:
    yaml.dump(yaml_data, yaml_file, allow_unicode=True, default_flow_style=False)

print("Conversion complete.")
