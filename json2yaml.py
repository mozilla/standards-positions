import json
import yaml
import html

# Load the JSON data
with open('activities.json', 'r') as json_file:
    json_data = json.load(json_file)

# Convert to YAML format
yaml_data = {}

for item in json_data:
    title = html.unescape(item['title'])
    yaml_data[title] = {
        'id': item['id'],
        'description': html.unescape(item['description']),
        'rationale': html.unescape(item['mozPositionDetail']) if item['mozPositionDetail'] else None,
        'bug': item['mozBugUrl'],
        'position': item['mozPosition'],
        'issue': item['mozPositionIssue'],
        'venues': [ item['org'] ],
        'url': item['url'],
        'caniuse': item['ciuName']
    }

# Save as YAML
with open('activities.yml', 'w') as yaml_file:
    yaml.dump(yaml_data, yaml_file, allow_unicode=True, default_flow_style=False)

print("Conversion complete.")
