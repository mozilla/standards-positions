import yaml
import re
import sys
import argparse
import requests
from typing import Any, Dict, List, Tuple

class YAMLValidator:
    def __init__(self, file_path: str, fix: bool = False):
        self.file_path = file_path
        self.fix = fix
        self.issues = set()
        self.errors = []
        self.modified_data = None

    def load_yaml(self) -> Tuple[Dict[str, Any], Dict[int, str]]:
        try:
            with open(self.file_path, 'r') as file:
                lines = file.readlines()
                data = yaml.safe_load("".join(lines))
                line_map = {i + 1: line.strip() for i, line in enumerate(lines)}
                return data, line_map
        except yaml.YAMLError as e:
            raise ValueError("Failed to load YAML: Invalid YAML format") from e

    def log_error(self, message: str, key: str = "", line: int = None, fixable=False):
        tofix = " (Use --fix to fix.)" if fixable else ""
        if line is not None:
            self.errors.append(f"Error at line {line} in key '{key}': {message}{tofix}")
        else:
            self.errors.append(f"Error: {message}{tofix}")

    def validate_top_level_keys(self, data: Dict[str, Any], line_map: Dict[int, str]):
        keys = list(data.keys())
        modified = False

        # Check for non-string keys
        non_string_keys = [key for key in keys if not isinstance(key, str)]
        if non_string_keys:
            for key in non_string_keys:
                line_num = next((line for line, content in line_map.items() if str(key) in content), None)
                self.log_error("Top-level keys must be strings", key, line_num)

        # Check alphabetical order
        if keys != sorted(keys):
            if self.fix:
                data = dict(sorted(data.items()))
                modified = True
            else:
                self.log_error("Top-level keys must be in alphabetical order.", fixable=True)

        # Check for unique keys
        unique_keys = set(keys)
        if len(keys) != len(unique_keys):
            duplicates = [key for key in keys if keys.count(key) > 1]
            for key in set(duplicates):
                line_num = next((line for line, content in line_map.items() if key in content), None)
                self.log_error("Top-level keys must be unique", key, line_num)

        if self.fix and modified:
            self.modified_data = data  # Track modified data for saving later

    def validate_item(self, item: Dict[str, Any], key: str, line: int):
        modified = False

        # Validate issue (required and unique)
        if 'issue' not in item:
            self.log_error("Missing required 'issue' key", key, line)
        elif not isinstance(item['issue'], int):
            self.log_error(f"'issue' must be a unique number, got {item['issue']}", key, line)
        elif item['issue'] in self.issues:
            self.log_error(f"'issue' {item['issue']} is not unique", key, line)
        else:
            self.issues.add(item['issue'])

        # Validate rationale (optional but must be string if present)
        if 'rationale' in item and item['rationale'] is not None:
            if not isinstance(item['rationale'], str):
                self.log_error(f"'rationale' must be a string, got {item['rationale']}", key, line)

        # Legacy item key restriction for issue numbers >= 1110
        if 'issue' in item and item['issue'] >= 1110:
            for legacy_key in ['position', 'venues']:
                if legacy_key in item:
                    if self.fix:
                        item.pop(legacy_key, None)
                        modified = True
                    else:
                        self.log_error(f"Legacy key {legacy_key}. Please use GitHub issue labels instead.", key, line, fixable=True)

        # Optional fields validation
        if 'id' in item and (not isinstance(item['id'], str) or ' ' in item['id']):
            self.log_error(f"'id' must be a string without whitespace, got {item['id']}", key, line)
        if 'description' in item and item['description'] not in [None, '']:
            if not isinstance(item['description'], str) or not item['description'].strip():
                self.log_error(f"'description' must be a string or null, got {item['description']}", key, line)
        if 'bug' in item and item['bug'] not in [None, '']:
            if not isinstance(item['bug'], str) or not item['bug'].startswith("https://bugzilla.mozilla.org/show_bug.cgi?id="):
                self.log_error(f"'bug' must be a URL starting with 'https://bugzilla.mozilla.org/show_bug.cgi?id=', got {item['bug']}", key, line)
        if 'caniuse' in item and item['caniuse'] not in [None, '']:
            if not isinstance(item['caniuse'], str) or not item['caniuse'].startswith("https://caniuse.com/"):
                self.log_error(f"'caniuse' must be a URL starting with 'https://caniuse.com/' or empty, got {item['caniuse']}", key, line)
        if 'position' in item and item['position'] not in {"positive", "neutral", "negative", "defer", "under consideration"}:
            self.log_error(f"'position' must be one of the allowed values, got {item['position']}", key, line)
        if 'url' in item and not item['url'].startswith("https://"):
            self.log_error(f"'url' must start with 'https://', got {item['url']}", key, line)
        if 'venues' in item:
            allowed_venues = {"WHATWG", "W3C", "W3C CG", "IETF", "Ecma", "Unicode", "Proposal", "Other"}
            if not isinstance(item['venues'], list) or not set(item['venues']).issubset(allowed_venues):
                self.log_error(f"'venues' must be a list with allowed values, got {item['venues']}", key, line)

        return modified

    def validate_data(self, data: Dict[str, Any], line_map: Dict[int, str]):
        modified = False
        for key, item in data.items():
            start_line = next((line for line, content in line_map.items() if key in content), None)
            if start_line is not None:
                if self.validate_item(item, key, start_line):
                    modified = True

        if self.fix and modified:
            self.modified_data = data  # Track modified data for saving later

    def save_fixes(self):
        if self.modified_data:
            with open(self.file_path, 'w') as file:
                yaml.dump(self.modified_data, file, allow_unicode=True, default_flow_style=False)
            print(f"Fixes applied and saved to {self.file_path}")

    def run(self):
        data, line_map = self.load_yaml()
        self.validate_top_level_keys(data, line_map)
        self.validate_data(data, line_map)

        if self.errors:
            print("YAML validation failed with the following errors:")
            for error in self.errors:
                print(error)
            sys.exit(1)
        else:
            if self.fix:
                self.save_fixes()
            # No success message on pass if not fixing

    def add_issue(self, issue_num: int, description: str = None, rationale: str = None):
        # Fetch issue data from GitHub
        url = f"https://api.github.com/repos/mozilla/standards-positions/issues/{issue_num}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Failed to fetch issue {issue_num}: {response.status_code}")
            sys.exit(1)

        issue_data = response.json()
        title = issue_data.get("title")

        if not title:
            print("No title found in the GitHub issue data.")
            sys.exit(1)

        # Load current YAML data
        data, _ = self.load_yaml()

        # Find if the issue already exists
        issue_exists = False
        for key, item in data.items():
            if item.get('issue') == issue_num:
                item['description'] = description if description is not None else item.get('description')
                item['rationale'] = rationale if rationale is not None else item.get('rationale')
                issue_exists = True
                break

        # Add new entry if the issue does not exist
        if not issue_exists:
            data[title] = {
                "issue": issue_num,
                "description": description,
                "rationale": rationale
            }

        # Sort and save changes
        data = dict(sorted(data.items()))
        with open(self.file_path, 'w') as file:
            yaml.dump(data, file, allow_unicode=True, default_flow_style=False)
        print(f"Issue {issue_num} added or updated successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage activities.yml.")
    parser.add_argument("command", choices=["validate", "add"], help="Specify 'validate' to validate or 'add' to add or update an item.")
    parser.add_argument("issue_num", nargs="?", type=int, help="Issue number for the 'add' command.")
    parser.add_argument("--fix", action="store_true", help="Automatically fix issues (sort and drop legacy keys)")
    parser.add_argument("--description", type=str, help="Set the description for the issue.")
    parser.add_argument("--rationale", type=str, help="Set the rationale for the issue.")
    args = parser.parse_args()

    if args.command == "validate":
        validator = YAMLValidator("activities.yml", fix=args.fix)
        try:
            validator.run()
        except ValueError as e:
            print(f"Validation failed: {e}")
    elif args.command == "add":
        if args.issue_num is None:
            print("Please provide an issue number for 'add'.")
            sys.exit(1)
        validator = YAMLValidator("activities.yml")
        validator.add_issue(args.issue_num, description=args.description, rationale=args.rationale)
