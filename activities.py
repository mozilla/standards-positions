from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.scalarstring import LiteralScalarString
import argparse
import requests
import sys
from typing import Any, Dict


class YAMLValidator:
    def __init__(self, file_path: str, fix: bool = False):
        self.file_path = file_path
        self.fix = fix
        self.errors = []
        self.modified_data = None
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.width = float("inf")  # prevent line breaks between key and value

    def load_yaml(self) -> CommentedMap:
        try:
            with open(self.file_path, 'r') as file:
                data = self.yaml.load(file)
                return data
        except Exception as e:
            raise ValueError(f"Failed to load YAML: {e}") from e

    def log_error(self, message: str, key: str = ""):
        self.errors.append(f"Error in key '{key}': {message}")

    def validate_top_level_keys(self, data: CommentedMap):
        keys = list(data.keys())
        if keys != sorted(keys):
            if self.fix:
                self.modified_data = CommentedMap(sorted(data.items()))
            else:
                self.log_error("Top-level keys must be in alphabetical order.")

    def validate_literal_block(self, data: CommentedMap, key: str, field: str):
        value = data.get(key, {}).get(field)
        if value is not None:
            if not isinstance(value, LiteralScalarString):
                if self.fix:
                    data[key][field] = LiteralScalarString(value)
                else:
                    self.log_error(f"'{field}' must use literal block syntax (|).", key)
            elif not value.endswith('\n'):
                if self.fix:
                    data[key][field] = LiteralScalarString(f"{value}\n")
                else:
                    self.log_error(f"'{field}' must end with a newline to use '|' syntax.", key)

    def validate_item(self, data: CommentedMap, key: str):
        item = data[key]
        if not isinstance(item, dict):
            self.log_error(f"Item '{key}' must be a dictionary.", key)
            return

        # Validate required fields
        if 'issue' not in item:
            self.log_error("Missing required 'issue' key.", key)
        elif not isinstance(item['issue'], int):
            self.log_error(f"'issue' must be an integer, got {item['issue']}.", key)
        elif item['issue'] >= 1110:
            # Legacy item key restriction for issue numbers >= 1110
            for legacy_key in ['position', 'venues']:
                if legacy_key in item:
                    if self.fix:
                        del item[legacy_key]
                    else:
                        self.log_error(f"Legacy key '{legacy_key}' is not allowed for issue numbers >= 1110.", key)

        # Validate literal block fields
        for field in ['description', 'rationale']:
            self.validate_literal_block(data, key, field)

        # Optional fields validation
        if 'id' in item and (not isinstance(item['id'], str) or ' ' in item['id']):
            self.log_error(f"'id' must be a string without whitespace, got {item['id']}.", key)

        if 'bug' in item and item['bug'] not in [None, '']:
            if not isinstance(item['bug'], str) or not item['bug'].startswith("https://bugzilla.mozilla.org/show_bug.cgi?id="):
                self.log_error(f"'bug' must be a URL starting with 'https://bugzilla.mozilla.org/show_bug.cgi?id=', got {item['bug']}.", key)

        if 'caniuse' in item and item['caniuse'] not in [None, '']:
            if not isinstance(item['caniuse'], str) or not item['caniuse'].startswith("https://caniuse.com/"):
                self.log_error(f"'caniuse' must be a URL starting with 'https://caniuse.com/', got {item['caniuse']}.", key)

        if 'mdn' in item and item['mdn'] not in [None, '']:
            if not isinstance(item['mdn'], str) or not item['mdn'].startswith("https://developer.mozilla.org/en-US/"):
                self.log_error(f"'mdn' must be a URL starting with 'https://developer.mozilla.org/en-US/', got {item['mdn']}.", key)

        if 'position' in item and item['position'] not in {"positive", "neutral", "negative", "defer", "under consideration"}:
            self.log_error(f"'position' must be one of the allowed values, got {item['position']}.", key)

        if 'url' in item and not item['url'].startswith("https://"):
            self.log_error(f"'url' must start with 'https://', got {item['url']}.", key)

        if 'venues' in item:
            allowed_venues = {"WHATWG", "W3C", "W3C CG", "IETF", "Ecma", "Unicode", "Proposal", "Other"}
            if not isinstance(item['venues'], list) or not set(item['venues']).issubset(allowed_venues):
                self.log_error(f"'venues' must be a list with allowed values, got {item['venues']}.", key)

    def validate_data(self, data: CommentedMap):
        for key in data:
            self.validate_item(data, key)

        self.validate_top_level_keys(data)

        if self.fix and self.modified_data is None:
            self.modified_data = data

    def save_fixes(self):
        if self.modified_data:
            with open(self.file_path, 'w') as file:
                self.yaml.dump(self.modified_data, file)
            print(f"Fixes applied and saved to {self.file_path}")

    def run(self):
        data = self.load_yaml()
        self.validate_data(data)

        if self.errors:
            print("YAML validation failed with the following errors:")
            for error in self.errors:
                print(error)
            sys.exit(1)
        elif self.fix:
            self.save_fixes()

    def add_issue(self, issue_num: int, description: str = None, rationale: str = None):
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

        data = self.load_yaml()

        if title not in data:
            data[title] = {"issue": issue_num}

        if description:
            data[title]["description"] = LiteralScalarString(f"{description}\n")
        if rationale:
            data[title]["rationale"] = LiteralScalarString(f"{rationale}\n")

        # Sort keys alphabetically
        self.modified_data = CommentedMap(sorted(data.items()))
        with open(self.file_path, 'w') as file:
            self.yaml.dump(self.modified_data, file)
        print(f"Issue {issue_num} added or updated successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage activities.yml.")
    parser.add_argument("command", choices=["validate", "add"], help="Specify 'validate' to validate or 'add' to add or update an item.")
    parser.add_argument("issue_num", nargs="?", type=int, help="Issue number for the 'add' command.")
    parser.add_argument("--fix", action="store_true", help="Automatically fix issues.")
    parser.add_argument("--description", type=str, help="Set the description for the issue.")
    parser.add_argument("--rationale", type=str, help="Set the rationale for the issue.")
    args = parser.parse_args()

    validator = YAMLValidator("activities.yml", fix=args.fix)

    if args.command == "validate":
        try:
            validator.run()
        except ValueError as e:
            print(f"Validation failed: {e}")
    elif args.command == "add":
        if args.issue_num is None:
            print("Please provide an issue number for 'add'.")
            sys.exit(1)
        validator.add_issue(args.issue_num, description=args.description, rationale=args.rationale)
