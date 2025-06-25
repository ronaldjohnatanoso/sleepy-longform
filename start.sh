#!/bin/bash

# Set a user data directory relative to current working directory
USER_DATA_DIR="./chrome-profile1"
DEBUG_PORT=9222
BINARY_PATH="./chrome-lab/linux-116/chrome-linux64/chrome"
# Create the user data dir if it doesn't exist
mkdir -p "$USER_DATA_DIR"

# Start Chrome headless with remote debugging and persistent profile
$BINARY_PATH \
  --remote-debugging-port=$DEBUG_PORT \
  --user-data-dir="$USER_DATA_DIR" \
  --no-first-run \
  --no-default-browser-check \
  --disable-default-apps \
  --disable-background-networking \
  --safebrowsing-disable-auto-update \
  --disable-component-update \
  --password-store=basic \
  --use-mock-keychain \
  --disable-popup-blocking \
  --disable-features=ChromeWhatsNewUI
