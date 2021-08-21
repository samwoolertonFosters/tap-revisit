# tap-sitehq

This is a [Singer](https://singer.io) tap that produces JSON-formatted
data from the [SiteHQ](http://sitehq.nz/) API following the [Singer
spec](https://github.com/singer-io/getting-started/blob/master/SPEC.md).

This is the official data pipeline for SiteHQ, maintained by the company.

This tap:

- Pulls raw data from the [SiteHQ API](https://sitehq-docs.netlify.app/)
- Extracts the following resources from SiteHQ:
  - sites
  - visits
  - users
- Outputs the schema for each resource
- Incrementally pulls data based on the input state

## Quick start

1. Install

   We recommend using a virtualenv:

   ```bash
   > virtualenv -p python3 venv
   > source venv/bin/activate
   > pip install -e .
   ```

2. Get your SiteHQ API key

A SiteHQ API key is required to use `tap-sitehq`, and these API keys can be created by anyone with the company admin role.

3. Create the config file

   Create a JSON file called `config.json` containing the access token you were provided.

   ```json
   { "api_key": "yourapikey" }
   ```

4. Run the tap in discovery mode to get properties.json file

   ```bash
   tap-sitehq --config config.json --discover > properties.json
   ```

5. In the properties.json file, select the streams to sync

   Each stream in the properties.json file has a "schema" entry. To select a stream to sync, add `"selected": true` to that stream's "schema" entry. For example, to sync the `sites` stream:

   ```
   ...
   "tap_stream_id": "sites",
   "schema": {
     "selected": true,
     "properties": {
   ...
   ```

6. Run the application

   `tap-sitehq` can be run with:

   ```bash
   tap-sitehq --config config.json --properties properties.json
   ```
