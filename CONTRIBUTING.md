# How Can I Help?

We welcome contributions from the Mozilla community about its position on Web specifications.

## Requesting a Mozilla Position on a Web Specification

If there is a public, Web-related specification that you think Mozilla might be interested in,
please
[open a new issue](https://github.com/mozilla/standards-positions/issues/new),
filling out the auto-included template appropriately. (If posting via GitHub API, please copy the
[template](https://github.com/mozilla/standards-positions/blob/main/ISSUE_TEMPLATE.md)
and fill it out).

Normally, the appropriate granularity for an issue is a distinct web platform feature. This could
be a section of a specification, a single specification, or crossing multiple specifications. If an
effort involves multiple, tightly integrated specs, one can be created for the "main" document, and
include the others in the description.

Please understand that this repository is **only** for requests to determine a Mozilla position on
a technical specification. For all other issues, see [bugzilla](https://bugzilla.mozilla.org) or
the specification's issues list. Coordinators will close invalid and duplicate issues without
discussion.

It's also **not a specification review process**; please understand if detailed suggestions or
feedback are not forthcoming (although they might sometimes be given).

### Which Specifications?

Specifications that are relevant to Web browsers like Mozilla are in-scope here; non-browser
specifications (while great for the Web) are not, and will be marked `invalid`.

To be considered, a specification needs to be published under well-understood IPR terms, 
and should generally be on a standards track. 
This currently includes:

* Ecma TC39 proposals
* IETF RFCs and Internet-Drafts
* W3C Working Drafts and (Candidate) Recommendations
* WHATWG Living Standards (typically we consider change proposals)

We may also provide positions on documents located outside a standards process, 
e.g. W3C Notes, or those in W3C Community Groups such as [WICG](https://wicg.github.io/) 
or other community incubation efforts with well-understood
<abbr title="intellectual property rights">IPR</abbr> terms. 
As a general rule we believe that any such work must be moved to a formal standards track 
before it’s appropriate for adoption as part of the web platform.

If a specification has been abandoned, deprecated, or obsoleted by its publishing body, this generally
indicates that it is not under consideration.

If a specification is already implemented by Mozilla (or is in the development process), it
typically won't be necessary to determine a Mozilla position on it, since we're already devoting
resources to it.

### Making a Position Request

New specifications can be added by opening a new issue.

### Asking Mozilla to Update a Position

Specifications might be updated after a position is decided. Updates to a
specification could justify a new position, especially if those updates are in
response to feedback provided by Mozilla.

If you think that changes to a proposal warrant an updated position from
Mozilla, please request another review by commenting on the original issue for
the specification. Please include a summary of the changes that you believe to
be relevant. A closed issue will be reopened if Mozilla agrees to make another
assessment.

## Discussing Mozilla's Position on a Web Specification

### For the Broader Community

We welcome discussion from members of the wider Mozilla community -- including the public -- but ask
that it be on-topic, and that it follow [Mozilla's Community Participation
Guidelines](https://www.mozilla.org/about/governance/policies/participation/).

Specifically, the primary purpose of this repository is to determine Mozilla's postions on
specifications. That is distinct from the larger Web community's position; the best place to
advocate for a specification is using the appropriate standards body's discussion mechanisms, not
here.

We expect that cited resources (such as an explainer or proposed specification)
include all the information necessary to understand the proposal:
the problem that is being addressed or use-cases of interest;
the shape of the proposed solution;
an explanation of how the proposal addresses the problem;
and how the proposal might affect the system as a whole.
Issues should only provide a high-level summary of this information in a couple of sentences at most.

Please focus your comments on bringing new information about a specification.

If you want to express support for a specification, the best way to do that is using [Github
reactions](https://github.com/blog/2119-add-reactions-to-pull-requests-issues-and-comments) on the
issue or a specific comment.

If you want to ask about (or contribute to) Firefox support for a specification, please use
the respective Bugzilla bug, linked in the standards-position dashboard entry / the GitHub issue.

If an issue becomes overwhelmed by excessive advocacy or other off-topic comments,
comments might be hidden, edited, or deleted, and the issue might be locked.

### For Mozilla's Subject-Matter Experts

The purpose of this repository is to help
Mozilla's technical leaders reach a consensus position
about new Web features being proposed.
Therefore, you might be asked for your opinion
on specifications where you are one of the experts within the Mozilla community,
or feel like you have valuable contributions to make
to issues on other specifications even where you haven't explicitly been asked to do so.

The goal of the discussions in this repository is
to figure out what we think about a proposal or specification.
The key factors to consider are:

* how useful we think the proposed feature is likely to be (or how important the use-cases it's trying to address are), relative to the likely costs to users (e.g., security or privacy risks), developers (e.g., increased complexity and cognitive load), and implementers (cost of implementing it and maintaining that implementation)
* whether there are any critical problems we see in the current proposal that we should try to get fixed (e.g., around security, privacy, or ability to implement across multiple browser engines)

It's useful to discuss these in the relevant issue in this repository.

At the same time,
we should avoid causing
discussions that should happen in the standards body's normal discussion mechanisms
to happen instead in the standards-positions issue.
When it makes sense to do so,
it's good to raise issues through the normal issue trackers for the proposal.
However, when doing so, it's worth being careful to avoid giving a *false impression*
that engagement in the discussion constitutes support.
In some cases, avoiding this impression may require having some of the discussion in the standards-positions issue.
However, in many cases that can be avoided
by giving appropriate context when filing issues, such as:
"I was reading [specification] in order to understand it better
to help evaluate what Mozilla thinks of it,
and while doing that I noticed ..."

#### Propose a position

Add a comment in the issue with a summary of any concerns, a proposed position, and rationale (as appropriate).

If you have [permission to add labels](https://github.com/orgs/mozilla/teams/standards-contributor), you can add "topic:", "concerns:", "venue:" labels. These will show up in the dashboard.

The maintainers of this repo will add the appropriate "position:" label to the issue after 7 days if there's no disagreement, and then either close the issue or ask for a PR to add detailed rationale to the dashboard (see below).

#### Add a rationale to the dashboard

Some standards positions should have a recorded rationale in the dashboard. This is recorded in the `activities.yml` file.

To add an item to `activities.yml` or to update the rationale of an existing item, run:

```
python3 activities.py add 1234 --rationale "..."
```

...where 1234 is the GitHub issue number. Optionally also add `--description "..."` to add a description of the feature or specification.

Alternatively, edit `activities.yml` directly. The `description` and `rationale` fields support a subset of markdown: inline code and links (URL must start with `#` or `https://`).

Then submit a pull request with the changes.

We'd like to try to keep the technical discussion
about the position
in the issue itself
(so that it stays in one place),
and limit the discussion in the pull request
to the details of making the change to `activities.yml`,
and accurately communicating the consensus in the issue.

Similarly, when changes to a proposal warrant an updated position and
there is sufficient consensus in subsequent comments on the issue,
make a pull request to document that updated consensus by changing `activities.yml`.

Tips:
* Specification URLs should link to a living standard or editor’s draft if available.
