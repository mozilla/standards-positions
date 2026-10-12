from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.scalarstring import LiteralScalarString
import argparse
import io
import os
import re
import requests
import sys
from typing import Any, Dict

# Retrieve the token from environment variables
token = os.getenv('GITHUB_TOKEN')
headers = {"Authorization": f"token {token}"} if token else {}

SMART_TO_STRAIGHT = {
    '”': '"',
    '“': '"',
    '’': "'",
    '‘': "'",
}

# Same as linkPattern and codePattern in index.html, minus the URL restriction
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^\)]+)\)")
CODE_PATTERN = re.compile(r"`([^`]+)`")


def straighten(s: str) -> str:
    for k, v in SMART_TO_STRAIGHT.items():
        s = s.replace(k, v)
    return s


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
                    value = data[key][field]
                else:
                    self.log_error(f"'{field}' must use literal block syntax (|).", key)
                    return
            if not value.endswith('\n'):
                if self.fix:
                    data[key][field] = LiteralScalarString(f"{value}\n")
                    value = data[key][field]
                else:
                    self.log_error(f"'{field}' must end with a newline to use '|' syntax.", key)
                    return

            s = str(value)
            replaced = straighten(s)
            if replaced != s:
                if self.fix:
                    data[key][field] = LiteralScalarString(replaced)
                else:
                    self.log_error(
                        f"'{field}' contains smart quotes; replace them with straight quotes (\" or ').",
                        key
                    )

            for match in LINK_PATTERN.finditer(CODE_PATTERN.sub("code", s)):
                if not match.group(2).startswith(("#", "https://")):
                    self.log_error(f"'{field}' link URL must start with '#' or 'https://', got {match.group(2)}.", key)

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
        if 'id' in item and (not isinstance(item['id'], str) or any(c.isspace() for c in item['id'])):
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

        if 'url' in item and item['url'] not in [None, '']:
            if not isinstance(item['url'], str) or not item['url'].startswith("https://"):
                self.log_error(f"'url' must start with 'https://', got {item['url']}.", key)

        if 'venues' in item:
            allowed_venues = {"WHATWG", "W3C", "W3C CG", "IETF", "Ecma", "Unicode", "Proposal", "Other"}
            if not isinstance(item['venues'], list) or not set(item['venues']).issubset(allowed_venues):
                self.log_error(f"'venues' must be a list with allowed values, got {item['venues']}.", key)

    def validate_data(self, data: CommentedMap):
        keys_by_issue = {}
        for key in data:
            self.validate_item(data, key)
            issue = data[key].get('issue') if isinstance(data[key], dict) else None
            if isinstance(issue, int):
                keys_by_issue.setdefault(issue, []).append(key)

        for issue, keys in keys_by_issue.items():
            for key in keys[1:]:
                self.log_error(f"Duplicate 'issue' {issue}, also used by '{keys[0]}'.", key)

        self.validate_top_level_keys(data)

        if self.fix and self.modified_data is None:
            self.modified_data = data

    def save_fixes(self):
        if self.modified_data:
            output = io.StringIO()
            self.yaml.dump(self.modified_data, output)
            with open(self.file_path, 'r') as file:
                if file.read() == output.getvalue():
                    return
            with open(self.file_path, 'w') as file:
                file.write(output.getvalue())
            print(f"Fixes applied and saved to {self.file_path}")

    def run(self):
        data = self.load_yaml()
        self.validate_data(data)

        if self.fix:
            self.save_fixes()

        if self.errors:
            print("YAML validation failed with the following errors:")
            for error in self.errors:
                print(error)
            sys.exit(1)

    def add_issue(self, issue_num: int, description: str = None, rationale: str = None):
        url = f"https://api.github.com/repos/mozilla/standards-positions/issues/{issue_num}"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"Failed to fetch issue {issue_num}: {response.status_code}")
            sys.exit(1)

        issue_data = response.json()
        title = issue_data.get("title")

        if not title:
            print("No title found in the GitHub issue data.")
            sys.exit(1)

        data = self.load_yaml()

        # Reuse an existing entry for this issue, even if the issue title has changed
        key = next((k for k, v in data.items() if isinstance(v, dict) and v.get("issue") == issue_num), title)
        if key not in data:
            data[key] = {"issue": issue_num}
        elif data[key].get("issue") != issue_num:
            print(f"Key '{key}' is already used by issue {data[key].get('issue')}.")
            sys.exit(1)

        if description:
            data[key]["description"] = LiteralScalarString(f"{straighten(description)}\n")
        if rationale:
            data[key]["rationale"] = LiteralScalarString(f"{straighten(rationale)}\n")

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
            sys.exit(1)
    elif args.command == "add":
        if args.issue_num is None:
            print("Please provide an issue number for 'add'.")
            sys.exit(1)
        validator.add_issue(args.issue_num, description=args.description, rationale=args.rationale)
