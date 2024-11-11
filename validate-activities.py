import yaml
import re
from typing import Any, Dict, List, Tuple
import sys

class YAMLValidator:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.issues = set()
        self.errors = []

    def load_yaml(self) -> Tuple[Dict[str, Any], Dict[int, str]]:
        try:
            with open(self.file_path, 'r') as file:
                lines = file.readlines()
                data = yaml.safe_load("".join(lines))
                line_map = {i + 1: line.strip() for i, line in enumerate(lines)}
                return data, line_map
        except yaml.YAMLError as e:
            raise ValueError("Failed to load YAML: Invalid YAML format") from e

    def log_error(self, message: str, key: str = "", line: int = None):
        if line is not None:
            self.errors.append(f"Error at line {line} in key '{key}': {message}")
        else:
            self.errors.append(f"Error: {message}")

    def validate_top_level_keys(self, data: Dict[str, Any], line_map: Dict[int, str]):
        keys = list(data.keys())

        # Check for non-string keys
        non_string_keys = [key for key in keys if not isinstance(key, str)]
        if non_string_keys:
            for key in non_string_keys:
                line_num = next((line for line, content in line_map.items() if str(key) in content), None)
                self.log_error("Top-level keys must be strings", key, line_num)

        # Check alphabetical order
        if keys != sorted(keys):
            for i, key in enumerate(keys):
                if key != sorted(keys)[i]:
                    line_num = next((line for line, content in line_map.items() if key in content), None)
                    self.log_error("Top-level keys must be in alphabetical order", key, line_num)

        # Check for unique keys
        unique_keys = set(keys)
        if len(keys) != len(unique_keys):
            duplicates = [key for key in keys if keys.count(key) > 1]
            for key in set(duplicates):
                line_num = next((line for line, content in line_map.items() if key in content), None)
                self.log_error("Top-level keys must be unique", key, line_num)

    def validate_item(self, item: Dict[str, Any], key: str, line: int):
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
            if 'position' in item:
                self.log_error("Please use GitHub issue labels instead.", key, line)
            if 'venues' in item:
                self.log_error("Please use GitHub issue labels instead.", key, line)

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

    def validate_data(self, data: Dict[str, Any], line_map: Dict[int, str]):
        for key, item in data.items():
            start_line = next((line for line, content in line_map.items() if key in content), None)
            if start_line is not None:
                self.validate_item(item, key, start_line)

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
            # No message on success.
            pass

if __name__ == "__main__":
    validator = YAMLValidator("activities.yml")
    try:
        validator.run()
    except ValueError as e:
        print(f"Validation failed: {e}")
