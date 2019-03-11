
# How Can I Help?

We welcome contributions from the Mozilla community about its position on Web specifications.

## Requesting a Mozilla Position on a Web Specification

If there is a public, Web-related specification that you think Mozilla might be interested in,
please open a new issue, filling out the template appropriately.

Normally, the appropriate granularity for an issue is a single specification; however, if an effort
involves multiple, tightly integrated specs, one can be created for the "main" document, and include
the others in the description.

Please understand that this repository is **only** for requests to determine a Mozilla position on
a technical specification. For all other issues, see [bugzilla](https://bugzilla.mozilla.org) or
the specification's issues list. Coordinators will close invalid and duplicate issues without
discussion.

It's also **not a specification review process**; please understand if detailed suggestions or
feedback are not forthcoming (although they might sometimes be given).

### Which Specifications?

Specifications that are relevant to Web browsers like Mozilla are in-scope here; non-browser
specifications (while great for the Web) are not, and will be marked `invalid`.

To be considered, a specification needs to be published under well-understood IPR terms. This
currently includes:

* Ecma TC39 proposals
* IETF RFCs and Internet-Drafts
* W3C drafts, Recommendations and Notes (including Community Group documents, specifically the WICG)
* WHATWG Living Standards (typically we consider change proposals)

If a specification has been abandoned, deprecated, or obsoleted by its publishing body, this generally
indicates that it is not under consideration.

If a specification is already implemented by Mozilla (or is in the development process), it
typically won't be necessary to determine a Mozilla position on it, since we're already devoting
resources to it.

### Making a Position Request

New specifications can be added by opening a new issue, or by making a pull request with the
appropriate details in the `activities.json` file.

If you decide to make a pull request, the `activities.py` script can help to fill in some of the
relevant details:

```
    > ./activities.py add https://example.com/url_to_the_spec
```

If successful, it will modify `activities.json` with the new specification. Check the json file to make sure that the appropriate details are present:

```
{
  "ciuName": "The short tagname from caniuse.com for the feature, if available",
  "description": "A textual description; often, the spec's abstract",
  "mozBugUrl": "The URL of the Mozilla bug tracking this specification, if available",
  "mozPosition": "under consideration",
  "mozPositionIssue": the number of the issue in this repo, if available,
  "mozPositionDetail": "more information about Mozilla's position",
  "org": one of ['IETF', 'W3C', 'WHATWG', 'Ecma', 'Other'],
  "title": "The spec's title",
  "url": "The canonical URL for the most recent version of the spec"
}
```

### Asking Mozilla to Update a Position

Specifications might be updated after a position is decided. Especially if those
updates are in response to feedback provided by Mozilla. If you think that
changes to a proposal warrant an updated position from Mozilla, please request
another review by commenting on the original issue for the specification. Please
include a summary of the changes that you believe to be relevant.

If you believe that you have new information that might cause Mozilla to
reconsider a position, provide that information and ask a coordinator to reopen
the issue.

## Discussing Mozilla's Position on a Web Specification

We welcome discussion members of the wider Mozilla community -- including the public -- but ask
that it be on-topic, and that it follow [Mozilla's Community Participation
Guidelines](https://www.mozilla.org/about/governance/policies/participation/).

Specifically, the primary purpose of this repository is to determine Mozilla's postions on
specifications. That is distinct from the larger Web community's position; the best place to
advocate for a specification is using the appropriate standards body's discussion mechanisms, not
here.

So, please focus your comments on bringing new information about a specification; if you want to
express support for adopting a specification, the best way to do that is using [Github
reactions](https://github.com/blog/2119-add-reactions-to-pull-requests-issues-and-comments) on the
issue or a specific comment.

If an issue becomes overwhelmed by excessive advocacy, comments might be deleted, and the
issue might be locked.

