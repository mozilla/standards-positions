#!/usr/bin/env python

# Based on https://github.com/WebKit/standards-positions/blob/main/summary.py

import json, os, requests, re, sys


# Utilities
def write_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2, separators=(",", ": "))
        f.write("\n")


# General processing
def process(issues):
    summary = []
    for issue in issues:
        if is_ignorable_issue(issue):
            continue

        summary_item = {"issue": int(issue["html_url"][issue["html_url"].rfind("/") + 1 :])}
        summary_item.update(process_labels(issue["labels"]))
        summary_item.update(process_body(issue))
        summary_item["title"] = re.sub(r"(request for (mozilla )?position|rfp)( ?:| on) ", "", issue["title"], flags=re.IGNORECASE)

        summary.append(summary_item)
    write_json("gh-data-summary.json", summary)
    print("Done: gh-data-summary.json.")


def is_ignorable_issue(issue):
    if "pull_request" in issue:
        return True
    for label in issue["labels"]:
        if label["name"] in ("duplicate", "invalid", "tooling", "proposal withdrawn"):
            return True
    return False


def process_labels(labels):
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


def get_url(text):
    # get the first url (maybe in markdown link) and remove trailing comma
    m = re.search(r"\b(https?://[^\)\s]+)", text)
    if m:
        url = m.group()
        if url.endswith(','):
            url = url[:-1]
        return url
    return ""

def process_body(issue):
    lines = issue["body"].splitlines()

    body = {
        "title": None,
        "url": None,
        "explainer": None,
        "mdn": None,
        "caniuse": None,
        "bug": None,
        "webkit": None,
    }

    mapping = {
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


    for line in lines:
        if line == "### Other information":
            break
        for title, key in mapping.items():
            text_title = f"* {title}: "
            if line.lower().startswith(text_title):
                value = line[len(text_title) :].strip()
                value = re.sub(r"\[[^\]]+\]\(([^\)]+)\)", r"\1", value)
                if key in ("url", "explainer", "mdn", "caniuse", "bug", "webkit"):
                    value = get_url(value)
                if value != "" and value.lower() != "n/a":
                    body[key] = value
                break
    return body


# Setup
def main():
    # update
    data = []
    page = 1
    while True:
        try:
            print(f"Fetching page {page}...")
            response = requests.get(
                f"https://api.github.com/repos/mozilla/standards-positions/issues?direction=asc&state=all&per_page=100&page={page}",
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
