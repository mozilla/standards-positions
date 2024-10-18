#!/usr/bin/env python

# Based on https://github.com/WebKit/standards-positions/blob/main/summary.py

import argparse, json, os, requests, re


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
        summary_item["title"] = re.sub(r"Request for [Pp]osition: ", "", issue["title"])

        summary.append(summary_item)
    write_json("gh-data-summary.json", summary)


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
        if label["name"] == "blocked":
            # assert position is None
            position = "blocked"
        elif label["name"].startswith("position: "):
            # assert position is None
            position = label["name"][len("position: ") :]
        # Venue
        elif label["name"].startswith("venue: "):
            venues.append(label["name"][len("venue: ") :])
        # Concerns
        elif label["name"].startswith("concerns: "):
            concerns.append(label["name"][len("concerns: ") :])
        # Topics
        elif label["name"].startswith("topic: "):
            topics.append(label["name"][len("topic: ") :])

    return {
        "position": position,
        "venues": venues,
        "concerns": concerns,
        "topics": topics,
    }


def process_body(issue):
    lines = issue["body"].splitlines()

    body = {
        "title": None,
        "url": None,
        "explainer": None,
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
                if value != "" and value.lower() != "n/a":
                    body[key] = value
                break
    return body


# Setup
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="get the latest issue data from GitHub",
    )
    parser.add_argument("-p", "--process", action="store_true", help="process the data")
    args = parser.parse_args()

    if args.update:
        # GitHub allows us to read issues in increments of 100, called pages.
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
                print("Updated failed, network failure or request timed out.")
                exit(1)
            temp_data = response.json()
            if not temp_data:
                print("Empty!")
                break
            data.extend(temp_data)
            page += 1
        write_json("gh-data.json", data)
        print("Done updating.")
        exit(0)

    if args.process:
        if not os.path.exists("gh-data.json"):
            print("Sorry, you have to update first.")
            exit(1)

        with open("gh-data.json", "rb") as f:
            data = json.load(f)
        process(data)


if __name__ == "__main__":
    main()
