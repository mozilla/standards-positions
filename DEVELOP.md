# Develop

## Building locally

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

## GitHub Actions / Publishing

Publishing happens automatically when pushing to `main` as well as every 6 hours (to reflect any
changes to labels in GitHub) with the `build-and-deploy.yml` workflow. It can also be triggered
manually from the Actions page. This workflow needs a deploy key (Settings, Deploy keys), and the
private key stored as an environment secret named SSH_PRIVATE_KEY (Settings, Secrets and variables,
Actions).
