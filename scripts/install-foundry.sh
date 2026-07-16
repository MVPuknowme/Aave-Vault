#!/usr/bin/env bash
set -euo pipefail

# Installs Foundry toolchain (forge, cast, anvil) into a project-local directory.
# The target directory can be overridden via FOUNDRY_DIR, defaulting to .foundry.
FOUNDRY_DIR="${FOUNDRY_DIR:-.foundry}"
BIN_DIR="$FOUNDRY_DIR/bin"

if [ -x "$BIN_DIR/forge" ]; then
  echo "Foundry already installed at $BIN_DIR"
  exit 0
fi

echo "Installing Foundry into $FOUNDRY_DIR..."
FOUNDRY_DIR="$FOUNDRY_DIR" bash <(curl -fsSL https://foundry.paradigm.xyz)

if [ ! -x "$BIN_DIR/forge" ]; then
  echo "Foundry installation failed" >&2
  exit 1
fi

echo "Foundry installed: $($BIN_DIR/forge --version)"
