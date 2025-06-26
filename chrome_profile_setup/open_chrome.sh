#!/bin/bash

# PUT THE GMAIL ACCOUNT USERNAME HERE WITHOUT @GMAIL.COM
GMAIL_USERNAME="scytherkalachuchie"

# Set a user data directory relative to current working directory
USER_DATA_DIR="../profiles/$GMAIL_USERNAME"
DEBUG_PORT=9222
BINARY_PATH="../chrome_binary_setup/chrome/linux-116.0.5793.0/chrome-linux64/chrome"


# Create the user data dir if it doesn't exist
mkdir -p "$USER_DATA_DIR"

# Start Chrome headless with remote debugging and persistent profile
"$BINARY_PATH" \
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