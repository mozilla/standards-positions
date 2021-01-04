#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""\
Validate and add entries to activities.json, a file containing standards efforts that
are interesting to Mozilla.

Requires Python 3, BeautifulSoup 4, requests and html5lib; e.g.,

> pip3 install -r requirements.txt
"""

from __future__ import print_function
import json
import os
import re
import sys
import string
from urllib.parse import urlsplit, urlunsplit

try:
    from bs4 import BeautifulSoup
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError:
    sys.stderr.write("ERROR: Dependency not available. Try:\n")
    sys.stderr.write("       > pip3 install --user beautifulsoup4 requests html5lib\n\n")
    sys.exit(1)


# Github repo configuration
OWNER = "mozilla"
REPO = "standards-positions"

# Use a single encoder object so that we set it up with the single correct configuration for
# writing activities.json.
JSON_ENCODER = json.JSONEncoder(sort_keys=True, indent=2, separators=(",", ": "))


class IdType(object):
    "indicates an ID attribute."
    pass

class UrlType(object):
    "indicates a URL."
    pass

class UrlArrayType(object):
    "indicates a URL or array of URLs."
    pass


StringType = type(u"")
ArrayType = type([])


class ActivitiesJson(object):
    """
    A JSON file for activity tracking.
    """

    expected_entry_items = [  # (name, required?, type)
        ("id", True, IdType),
        ("title", True, StringType),
        ("description", True, StringType),
        ("ciuName", False, StringType),
        ("org", True, ["W3C", "IETF", "Ecma", "WHATWG", "Unicode", "Proposal", "Other"]),
        ("group", False, StringType),
        ("url", True, UrlType),
        ("mdnUrl", False, UrlArrayType),
        ("mozBugUrl", False, UrlArrayType),
        ("mozPositionIssue", True, int),
        (
            "mozPosition",
            True,
            [
                "under consideration",
                "important",
                "worth prototyping",
                "non-harmful",
                "defer",
                "harmful",
            ],
        ),
        ("mozPositionDetail", False, StringType),
    ]

    def __init__(self, filename):
        self.filename = filename
        self.data = None
        if filename:
            self.load()

    def load(self):
        "Load self.filename into self.data"
        try:
            with open(self.filename, "r") as rfh:
                self.data = json.load(rfh)
        except (OSError, IOError, ValueError) as why:
            sys.stderr.write("* ERROR: Can't load %s: %s\n" % (self.filename, why))
            sys.exit(1)

    def save(self):
        "Save self.data into self.filename"
        try:
            self.data.sort(key=lambda entry: entry["title"])
            with open(self.filename, "w") as wfh:
                wfh.write(JSON_ENCODER.encode(self.data))
                wfh.write("\n")
        except (OSError, IOError, ValueError) as why:
            sys.stderr.write("* ERROR: Can't write %s: %s\n" % (self.filename, why))
            sys.exit(1)

    def append(self, spec_entry):
        "Append a SpecEntry to self.data. Raises ValueError if it's malformed."
        errors = self.validate_entry(spec_entry.data, is_adding=True)
        if errors:
            raise ValueError(errors)
        self.data.append(spec_entry.data)

    def entry_unique(self, spec_entry):
        "Checks to see if there's a duplicate entry; raises ValueError if so."
        entry = spec_entry.data
        if entry["title"].lower().strip() in [
            e["title"].lower().strip() for e in self.data
        ]:
            raise ValueError(
                ["%s already contains title %s" % (self.filename, entry["title"])]
            )
        if entry["id"] in [e["id"] for e in self.data]:
            raise ValueError(
                ["%s already contains id %s" % (self.filename, entry["id"])]
            )
        if entry["url"] in [e["url"] for e in self.data]:
            raise ValueError(["%s already contains url %s" % (self.filename, entry["url"])])

    def validate(self, check_sorting):
        """
        Validate self.data for conformance to what we expect activities to be.

        Returns a list of errors encountered; empty list if it's clean.
        """
        if not isinstance(self.data, list):
            return ["Top-level data structure is not a list."]
        errors = []
        prevTitle = None
        i = 0
        for entry in self.data:
            i += 1
            if not isinstance(entry, dict):
                errors.append("Entry %i is not a dictionary." % i)
            title = entry.get("title", "entry %i" % i)
            errors = errors + self.validate_entry(entry, title)
            # This is *outside* validate_entry so that "add" can add an
            # entry with an empty ID (which must then be filled in), but
            # it will cause a validation error for other operations.
            if entry.get("id", "") == "":
                errors.append("{} includes has empty id".format(title))

            # Check that the entries are sorted by title, as save writes them.
            if check_sorting and prevTitle is not None and prevTitle > title:
                errors.append("{} is sorted incorrectly based on its title (it should not be after {})".format(title, prevTitle))
            prevTitle = title
        return errors

    def validate_entry(self, entry, title=None, is_adding=False):
        """
        Validate a single entry.

        Returns a list of errors encountered; empty if clean.
        """
        if not title:
            title = "Entry"
        errors = []
        for (name, required, value_type) in self.expected_entry_items:
            entry_value = entry.get(name, None)
            if required and not is_adding and entry_value is None:
                errors.append("%s doesn't have required member %s" % (title, name))
            else:
                if entry_value is None:
                    pass
                elif value_type == IdType:
                    if isinstance(entry_value, StringType):
                        for char in entry_value:
                            if char in string.whitespace:
                                errors.append("%s's %s contains whitespace" % (title, name))
                    else:
                        errors.append("%s's %s isn't a string." % (title, name))
                elif value_type == UrlType:
                    if isinstance(entry_value, StringType):
                        pass # FIXME: validate URL more?
                    else:
                        errors.append("%s's %s isn't a URL string." % (title, name))
                elif value_type == UrlArrayType:
                    if isinstance(entry_value, StringType):
                        pass # FIXME: validate URL more?
                    elif isinstance(entry_value, ArrayType):
                        for url in entry_value:
                            if isinstance(url, StringType):
                                pass # FIXME: validate URL more?
                            else:
                                errors.append("%s's %s isn't a URL string or array of them." % (title, name))
                    else:
                        errors.append("%s's %s isn't a URL string or array of them." % (title, name))
                elif isinstance(value_type, type):
                    if not isinstance(entry_value, value_type):
                        errors.append("%s's %s isn't a %s" % (title, name, value_type))
                elif isinstance(value_type, list):
                    if not entry_value in value_type:
                        errors.append(
                            "%s's %s isn't one of [%s]"
                            % (title, name, ", ".join(value_type))
                        )
                else:
                    raise ValueError("Unrecognized value type %s" % value_type)
            extra_items = set(entry.keys()) - set(
                [i[0] for i in self.expected_entry_items]
            )
            if extra_items:
                errors.append(
                    "%s includes unrecognized members: %s"
                    % (title, " ".join(extra_items))
                )
        return errors

    def __str__(self):
        return JSON_ENCODER.encode(self.data)


class SpecEntry(object):
    """
    Represents an entry for a single specification.
    """

    def __init__(self, spec_url):
        self.orig_url = spec_url
        self.data = {
            "id": u"",
            "title": "",
            "description": None,
            "ciuName": None,
            "org": "Proposal",
            "url": spec_url,
            "mdnUrl": None,
            "mozBugUrl": None,
            "mozPositionIssue": None,
            "mozPosition": u"under consideration",
            "mozPositionDetail": None,
        }
        self.parser = None
        self.figure_out_org()
        if self.parser:
            try:
                new_entry = self.fetch_spec_data(spec_url)
            except FetchError:
                sys.exit(1)
            self.data.update(**new_entry)

    def figure_out_org(self):
        """
        Figure out what organisation this belongs to and set self.parser.
        """
        host = urlsplit(self.orig_url).netloc.lower()
        if host in URL2ORG:
            self.parser = URL2ORG[host]
        elif host.endswith(".spec.whatwg.org"):
            self.parser = WHATWGParser
        else:
            sys.stderr.write(
                "* ERROR: Can't figure out what organisation %s belongs to! Using Proposal.\n" % host
            )

    def fetch_spec_data(self, url):
        """
        Fetch URL and try to parse it as a spec. Returns a spec_data dictionary.

        Can recurse if parsing raises BetterUrl.
        """
        res = requests.get(url)
        if res.status_code != 200:
            sys.stderr.write(
                "* Fetching spec resulted in %s HTTP status.\n" % res.status_code
            )
            raise FetchError
        soup = BeautifulSoup(res.text, "html5lib")
        try:
            spec_data = self.parser().parse(soup, url)
        except BetterUrl as why:
            new_url = why[0]
            sys.stderr.write("* Trying <%s>...\n" % new_url)
            spec_data = self.fetch_spec_data(new_url)
        except FetchError:
            sys.stderr.write("* Falling back.\n")
        return spec_data

    def create_issue(self):
        """
        Create a Github Issue for the entry. Returns the issue number if successful.
        """
        issue = {
            "title": self.data["title"],
            "body": """\
* Specification Title: {title}
* Specification URL: {url}
* MDN URL (optional): {mdnUrl}
* Bugzilla URL (optional): {mozBugUrl}
""".format(
                **self.data
            ),
        }
        gh_user = os.environ.get("GH_USER", None)
        gh_token = os.environ.get("GH_TOKEN", None)
        if not gh_user or not gh_token:
            sys.stderr.write(
                "* Cannot find GH_USER or GH_TOKEN; not creating an issue.\n"
            )
            return
        res = requests.post(
            "https://api.github.com/repos/%s/%s/issues" % (OWNER, REPO),
            data=json.dumps(issue),
            auth=HTTPBasicAuth(gh_token, gh_token),
        )
        if res.status_code != 201:
            sys.stderr.write("* Failed to create issue; status %s" % res.status_code)
            sys.exit(1)
        else:
            issue_num = res.json()["number"]
            self.data["mozPositionIssue"] = issue_num
            sys.stderr.write("* Created Github Issue %s\n" % issue_num)

    def __str__(self):
        return JSON_ENCODER.encode(self.data)


class BetterUrl(Exception):
    """
    We found a better URL for the specification.
    """

    pass


class FetchError(Exception):
    """
    We encountered a problem fetching the URL.
    """

    pass


class SpecParser(object):
    """
    Abstract Class for a Specification Parser.
    """

    org = None

    @staticmethod
    def clean_tag(tag):
        """
        Return a BeautifulSoup's tag contents as a string.
        """
        return re.sub("\n\s*", " ", tag.get_text()).strip()

    @staticmethod
    def clean_url(url):
        """
        Canonicalise a URL.
        """
        link = urlsplit(url)
        return "%s://%s%s" % (link.scheme, link.netloc.lower(), link.path)

    def parse(self, spec, url_string):
        """
        Parse a BeautifulSoup document for interesting things.

        Returns a dictionary.
        """
        raise NotImplementedError


class W3CParser(SpecParser):
    "Parser for W3C specs"
    org = "W3C"

    def get_link(self, spec, title):
        """
        Grab a link out of the W3C spec's metadata section.

        Returns None if not found.
        """
        title_exp = re.compile(title, re.IGNORECASE)
        metadata = spec.find("dl")
        try:
            link = (
                metadata.find("dt", string=title_exp).find_next_sibling("dd").a.string
            )
        except (TypeError, AttributeError):
            return None
        return self.clean_url(link)

    def parse(self, spec, url_string):
        data = {}
        refresh = spec.select('meta[http-equiv="Refresh"]')
        if refresh:
            raise BetterUrl(
                refresh[0].get("content").split(";", 1)[1].split("=", 1)[1].strip()
            )
        this_url = self.get_link(spec, "^This version")
        latest_url = self.get_link(spec, "^Latest version")
        ed_url = self.get_link(spec, "^Editor's draft")
        if ed_url and ed_url != this_url:
            raise BetterUrl(ed_url)
        elif latest_url and latest_url != this_url:
            raise BetterUrl(latest_url)
        elif this_url:
            data["url"] = this_url
        else:
            data["url"] = self.clean_url(url_string)
        data["org"] = self.org
        try:
            data["title"] = self.clean_tag(spec.h1)
        except AttributeError:
            try:
                data["title"] = self.clean_tag(spec.title)
            except AttributeError:
                sys.stderr.write("* Can't find the specification's title.\n")
                sys.exit(1)
        try:
            abstract_element = spec.find(id="abstract")
            if abstract_element.name != "section":
                abstract_element = abstract_element.find_next_sibling(["p", "div"])
            data["description"] = self.clean_tag(abstract_element)
        except AttributeError:
            sys.stderr.write("* Can't find the specification's description.\n")
            sys.exit(1)
        return data

class W3CCGParser(W3CParser):
    "Parser for W3C community group specs"
    org = "Proposal"

class WHATWGParser(W3CParser):
    "Parser for WHATWG specs"
    org = "WHATWG"


class IETFParser(SpecParser):
    "Parser for IETF specs"

    def get_meta(self, spec, names):
        """
        Get the `content` of a <meta> tag in the <head>.

        Takes a list of names that are tried in sequence; if none are present, None is returned.
        """
        try:
            name = names.pop(0)
        except IndexError:
            return None
        try:
            return spec.head.find("meta", attrs={"name": name})["content"].replace(
                "\n", " "
            )
        except (TypeError, AttributeError):
            return self.get_meta(spec, names)

    def parse(self, spec, url_string):
        url = urlsplit(url_string)
        path_components = url.path.split("/")
        if path_components[-1] == "":
            path_components.pop()
        if url.netloc.lower() == "tools.ietf.org":
            if path_components[1] in ["html"]:
                identifier = self.get_meta(spec, ["DC.Identifier"])
                if identifier.lower().startswith("urn:ietf:rfc"):
                    new_url = self.html_url("rfc%s" % identifier.rsplit(":", 1)[1])
                    if self.clean_url(url_string) != self.clean_url(new_url):
                        raise BetterUrl(
                            self.html_url("rfc%s" % identifier.rsplit(":", 1)[1])
                        )
                draft_name, draft_number = self.parse_draft_name(path_components[-1])
                if draft_number:
                    raise BetterUrl(self.html_url(draft_name))
            elif path_components[1] in ["id", "pdf"]:
                raise BetterUrl(self.html_url(path_components[2]))
            else:
                raise FetchError("I don't think that's a specification.")
        elif url.netloc.lower() == "www.ietf.org" and path_components[1] == "id":
            if path_components[1] in ["id", "pdf"]:
                try:
                    draft_name = path_components[2].rsplit(".", 1)[0]
                except ValueError:
                    draft_name = path_components[2]
                draft_name = self.parse_draft_name(draft_name)[0]
                raise BetterUrl(self.html_url(draft_name))
            else:
                raise FetchError("I don't think that's a specification.")
        elif url.netloc.lower() == "datatracker.ietf.org":
            if path_components[1] == "doc":
                raise BetterUrl(self.html_url(path_components[2]))
            else:
                raise FetchError("I don't think that's a specification.")
        data = {}
        data["title"] = self.get_meta(spec, ["DC.Title"]) or spec.head.title.string
        data["description"] = (
            self.get_meta(
                spec, ["description", "dcterms.abstract", "DC.Description.Abstract"]
            )
            or ""
        )
        is_ietf = draft_name.startswith("rfc") or draft_name.startswith("draft-ietf-") or draft_name.startswith("draft-irtf-")
        data["org"] = self.org = "IETF" if is_ietf else "Proposal"
        data["url"] = self.clean_url(url_string)
        return data

    @staticmethod
    def parse_draft_name(instr):
        "Parse a string into a draft name and number"
        try:
            draft_name, last_symbol = instr.rsplit("-", 1)
        except ValueError:
            return instr, None
        if last_symbol.isdigit() and len(last_symbol) == 2:
            return draft_name, last_symbol
        return instr, None

    @staticmethod
    def html_url(doc_name):
        "Return the canonical URL for a document name."
        path = "/".join(["html", doc_name])
        return urlunsplit(["https", "tools.ietf.org", path, "", ""])


# Map of URL hostnames to org-specific parsers.
URL2ORG = {
    "www.w3.org": W3CParser,
    "w3c.github.io": W3CParser,
    "wicg.github.io": W3CCGParser,
    "webbluetoothcg.github.io": W3CCGParser,
    "privacycg.github.io": W3CCGParser,
    "dev.w3.org": W3CParser,
    "dvcs.w3.org": W3CParser,
    "drafts.csswg.org": W3CParser,
    "drafts.css-houdini.org": W3CParser,
    "drafts.fxtf.org": W3CParser,
    "w3ctag.github.io": W3CParser,
    "immersive-web.github.io": W3CCGParser,
    "datatracker.ietf.org": IETFParser,
    "www.ietf.org": IETFParser,
    "tools.ietf.org": IETFParser,
    "http2.github.io": IETFParser,
    "httpwg.github.io": IETFParser,
    "httpwg.org": IETFParser,
}


def usage():
    "Display usage instructions and quit."
    sys.stderr.write(
        """\
USAGE: %s verb [args]
       Verbs:
         add      - Add an entry to activities.json and creates a Github issue;
                    requires a URL argument
         format   - Return the entry as JSON on STDOUT; requires a URL argument
         validate - Validate activities.json; no arguments
         sort     - Validate activities.json and write it out again in the
                    canonical sorted order.

To create Github Issues, GH_USER and GH_TOKEN must be in the environment;
to generate a token, see: <https://github.com/settings/tokens>. The
'public_repo' permission is required.

"""
        % sys.argv[0]
    )
    sys.exit(1)


if __name__ == "__main__":
    try:
        VERB = sys.argv[1]
    except IndexError:
        usage()

    if VERB not in ["validate", "add", "format", "sort"]:
        usage()

    if VERB in ["validate", "add", "sort"]:
        ACTIVITIES = ActivitiesJson("activities.json")
        ERRORS = ACTIVITIES.validate(check_sorting = (VERB != "sort"))
        if ERRORS:
            sys.stderr.write("\n".join(["* ERROR: %s" % E for E in ERRORS]) + "\n")
            sys.exit(1)

    if VERB in ["format", "add"]:
        if len(sys.argv) < 3:
            usage()
        try:
            SPEC_URL = unicode(sys.argv[2])  # python2
        except NameError:
            SPEC_URL = sys.argv[2]
        ENTRY = SpecEntry(SPEC_URL)
        if VERB == "format":
            print(ENTRY)
        elif VERB == "add":
            try:
                ACTIVITIES.entry_unique(ENTRY)
            except ValueError as unique_errors:
                sys.stderr.write("* ERROR: %s\n" % unique_errors[0][0])
                sys.exit(1)
            ENTRY.create_issue()
            ACTIVITIES.append(ENTRY)

    if VERB in ["add", "sort"]:
        ACTIVITIES.save()
