# Building locally

The data for the dashboard website is sourced from:

- The `activities.yml` file
- The GitHub issues in mozilla/standards-positions (text in OP, labels)

To fetch the GitHub information:

```
python3 gh-data.py
```

This will create or overwrite `gh-data.json` and `gh-data-summary.json`.

Then, to combine that data with the information in `activities.yml`:

```
python3 merge-data.py
```

This will create `merged-data.json` which is used by `index.html`.

To view the dashboard page locally, you need to start a local web server:

```
python3 -m http.server 8000
```

Then load http://localhost:8000/ in a web browser.

## Publishing

The generated JSON files are not added in the `main` branch.
However, the GitHub Actions workflow setup will build and push the generated files to the `gh-pages` branch,
to make it possible to review the history of the GitHub issue data.
That branch is then published using GitHub Pages.

The above happens on pushes to the `main` branch as well as when any labels are changed.
The latter runs the `labels-change.yml` workflow directly and then the `schedule-labels-change.yml` checks the history of workflow jobs to determine if labels have changed,
and if so pushes an empty commit to the `trigger-build` branch,
which causes the `build-and-deploy.yml` workflow to run.

The GitHub Actions need a deploy key (Settings, Deploy keys),
stored as an environment secret named SSH_PRIVATE_KEY (Settings, Secrets and variables, Actions).
