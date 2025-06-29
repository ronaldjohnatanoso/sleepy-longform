#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values - now relative to script location
PROFILES_DIR="$SCRIPT_DIR/../profiles"
USER_DATA_DIR=${1}
USER_DATA_DIR="$PROFILES_DIR/$USER_DATA_DIR" # Use first argument, fallback to env var
DEBUG_PORT="${2}" # Use second argument, fallback to env var
HEADLESS="${3:-false}" # Use third argument, default to false
BINARY_PATH="$SCRIPT_DIR/../chrome_binary_setup/chrome/linux-116.0.5793.0/chrome-linux64/chrome"

# Create the user data dir if it doesn't exist
mkdir -p "$USER_DATA_DIR"

echo "debug port: $DEBUG_PORT"
echo "headless mode: $HEADLESS"

if [ -z "$DEBUG_PORT" ]; then
  echo "Error: DEBUG_PORT is not set. Please provide it as an argument or set the environment variable."
  echo "Usage: $0 <user_data_dir> <debug_port> [headless]"
  exit 1
fi

# Kill any existing Chrome processes using this debug port
echo "Cleaning up existing Chrome processes on port $DEBUG_PORT..."
pkill -f "remote-debugging-port=$DEBUG_PORT" 2>/dev/null || true

# Wait a moment for processes to terminate
sleep 2

# Double-check and force kill if necessary
if pgrep -f "remote-debugging-port=$DEBUG_PORT" > /dev/null; then
  echo "Force killing remaining processes..."
  pkill -9 -f "remote-debugging-port=$DEBUG_PORT" 2>/dev/null || true
  sleep 1
fi

# Build Chrome command with base arguments
CHROME_ARGS=(
  --headless=new 
  --remote-debugging-port=$DEBUG_PORT
  --user-data-dir="$USER_DATA_DIR"
  --no-first-run
  --no-default-browser-check
  --disable-default-apps
  --disable-background-networking
  --safebrowsing-disable-auto-update
  --disable-component-update
  --password-store=basic
  --use-mock-keychain
  --disable-popup-blocking
  --disable-features=ChromeWhatsNewUI
  --disable-background-timer-throttling
  --disable-backgrounding-occluded-windows
  --disable-renderer-backgrounding
  --disable-dev-shm-usage
  --enable-webgl
  --enable-accelerated-2d-canvas
  --ignore-gpu-blacklist
  --disable-features=VizDisplayCompositor
  --enable-accelerated-video-decode
  --enable-accelerated-video-encode
  --enable-gpu-rasterization
  --enable-zero-copy
)

# Add headless-specific flags
if [ "$HEADLESS" = "true" ]; then
  CHROME_ARGS+=(
    --headless=new
    --disable-process-singleton-dialog
  )
  echo "Starting Chrome in headless mode..."
else
  echo "Starting Chrome with GUI..."
fi

# Start Chrome with the configured arguments
exec "$BINARY_PATH" "${CHROME_ARGS[@]}"