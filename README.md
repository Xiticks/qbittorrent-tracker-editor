# QbitUpdater

## Overview

`qbittorrent-tracker-editor` is a script designed to update a specified part of all trackers when it receives a webhook from an application in the \*arr suite giving the indexer name.

## Webhook

The script listens for the `update_tracker` webhook.

## Features

- Automatically updates the specified tracker.
- Handles indexer names that may contain the " (Prowlarr)" part, removing it as needed.

## Usage

1. Configure your \*arr application to send the `update_tracker` webhook to the script.
2. Ensure the indexer name is correctly specified, even if it includes " (Prowlarr)".

## Installation

### Docker

You can either build the image yourself or use the pre-built image from the Github Packages registry.

Using the docker-compose file, edit the environment variables to match your setup and run `docker-compose up -d`.

## Example

When the script receives the `update_tracker` webhook, it will process the indexer name and update the tracker accordingly.

## License

This project is licensed under the MIT License.
