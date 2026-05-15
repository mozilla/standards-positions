#!/usr/bin/env python

# Based on https://github.com/WebKit/standards-positions/blob/main/summary.py
import json, os, re
from collections.abc import Mapping, Sequence
from typing import Optional, Any

import requests

# Retrieve the token from environment variables
token = os.getenv('GITHUB_TOKEN')
headers = {"Authorization": f"token {token}"} if token else {}

Json = None | str | int | float | Sequence["Json"] | Mapping[str, "Json"]

# Utilities
def write_json(filename: str, data: Json) -> None:
    with open(filename, "w") as f:
        json.dump(data, f, indent=2, separators=(",", ": "))
        f.write("\n")


# General processing
def process(issues: list[Mapping[str, Any]]) -> None:
    summary = []
    for issue in issues:
        if is_ignorable_issue(issue):
            continue

        summary_item: dict[str, Any] = {"issue": int(issue["html_url"][issue["html_url"].rfind("/") + 1 :])}
        summary_item.update(process_labels(issue["labels"]))
        summary_item.update(process_body(issue))
        summary_item["title"] = re.sub(r"(request for (mozilla )?position|rfp)( ?:| on) ", "", issue["title"], flags=re.IGNORECASE)

        summary.append(summary_item)
    write_json("gh-data-summary.json", summary)
    print("Done: gh-data-summary.json.")


def is_ignorable_issue(issue: Mapping[str, Any]) -> bool:
    if "pull_request" in issue:
        return True
    for label in issue["labels"]:
        if label["name"] in ("duplicate", "invalid", "tooling", "proposal withdrawn"):
            return True
    return False


def process_labels(labels: list[Mapping[str, Any]]) -> Mapping[str, Optional[list[str]]]:
    position = None
    venues = []
    concerns = []
    topics = []

    for label in labels:
        # Position
        if label["name"].startswith("position: "):
            position = label["name"].split(": ")[1]
        # Venue
        elif label["name"].startswith("venue: "):
            venues.append(label["name"].split(": ")[1])
        # Concerns
        elif label["name"].startswith("concerns: "):
            concerns.append(label["name"].split(": ")[1])
        # Topics
        elif label["name"].startswith("topic: "):
            topics.append(label["name"].split(": ")[1])

    return {
        "position": position,
        "venues": venues,
        "concerns": concerns,
        "topics": topics,
    }


def get_url(text: str) -> str:
    # get the first url (maybe in markdown link) and remove trailing comma
    m = re.search(r"\b(https?://[^\)\s]+)", text)
    if m:
        url = m.group()
        if url.endswith(','):
            url = url[:-1]
        return url
    return ""


def get_feature_id(text: str) -> Optional[str]:
    if "https://" in text:
        url = get_url(text)
        url_prefixes = ["https://webstatus.dev/features/",
                         "https://web-platform-dx.github.io/web-features-explorer/"]
        for prefix in url_prefixes:
            if url.startswith(prefix):
                url = url.split("#", 1)[0].split("?", 1)[0]
                text = url[len(prefix):].split("/", 1)[0]
                break

    m = re.search("[a-z][a-zA-Z\-]+", text)
    if m:
        return m.group()
    return None


def process_body(issue: Mapping[str, Any]) -> Mapping[str, Optional[str]]:
    lines = issue["body"].splitlines()

    body: dict[str, Optional[str]] = {
        "title": None,
        "url": None,
        "explainer": None,
        "web-feature": None,
        "mdn": None,
        "caniuse": None,
        "bug": None,
        "webkit": None,
    }

    legacy_mapping = {
        # "specification title": "title",  # Always use the issue title
        "specification or proposal url (if available)": "url",
        "specification or proposal url": "url",
        "explainer url (if available)": "explainer",
        "explainer url": "explainer",
        "mdn url (optional)": "mdn",
        "caniuse.com url (optional)": "caniuse",
        "caniuse.com url": "caniuse",
        "bugzilla url (optional)": "bug",
        "bugzilla url": "bug",
        "webkit standards-position": "webkit",
    }

    yaml_mapping = {
        # Specification title
        "Specification or proposal URL (if available)": "url",
        "Explainer URL (if available)": "explainer",
        "web-feature id": "web-feature",
        "MDN URL": "mdn",
        "Caniuse.com URL": "caniuse",
        "Bugzilla URL": "bug",
        "WebKit standards-position": "webkit",
    }

    # Legacy issues using ISSUE_TEMPLATE.md
    if issue["number"] < 1175:
        for line in lines:
            if line == "### Other information":
                break
            for title, key in legacy_mapping.items():
                text_title = f"* {title}: "
                if line.lower().startswith(text_title):
                    value = line[len(text_title) :].strip()
                    if key in ("url", "explainer", "mdn", "caniuse", "bug", "webkit"):
                        value = get_url(value)
                    if value != "" and value.lower() != "n/a":
                        body[key] = value
                    break
    # Issues using YAML template
    else:
        response_field = None
        skip = False
        for line in lines:
            if line == "### Other information":
                break
            for title, key in yaml_mapping.items():
                text_title = f"### {title}"
                if line == text_title:
                    response_field = key
                    skip = True
                    break
            if skip:
                skip = False
                continue
            if response_field:
                value = line.strip()
                if response_field in ("url", "explainer", "mdn", "caniuse", "bug", "webkit"):
                    value = get_url(value)
                elif response_field == "web-feature":
                    value = get_feature_id(value)
                if value and value != "_No response_" and value.lower() != "n/a":
                    body[response_field] = value
                    response_field = None

    return body


# Setup
def main() -> None:
    # update
    data = []
    page = 1
    while True:
        try:
            print(f"Fetching page {page}...")
            response = requests.get(
                f"https://api.github.com/repos/mozilla/standards-positions/issues?direction=asc&state=all&per_page=100&page={page}",
                headers=headers,
                timeout=5,
            )
            response.raise_for_status()
        except Exception:
            print("Update failed, network failure or request timed out.")
            exit(1)

        temp_data = response.json()
        if not temp_data:
            print("Empty!")
            break
        data.extend(temp_data)

        # Check for 'link' header and 'rel="next"'
        link_header = response.headers.get("link", "")
        if 'rel="next"' not in link_header:
            break

        page += 1

    write_json("gh-data.json", data)
    print("Done: gh-data.json.")

    # process
    if not os.path.exists("gh-data.json"):
        print("Sorry, you have to update first.")
        exit(1)

    with open("gh-data.json", "rb") as f:
        data = json.load(f)
    process(data)


if __name__ == "__main__":
    main()
