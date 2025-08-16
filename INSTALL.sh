#!/usr/bin/env bash
set -euo pipefail

# Robust INSTALL.sh for POSIX systems
# - uses absolute repo paths
# - checks sources exist
# - uses rsync if available
# - updates user's shell profile safely (marker block)
# - adds universal alias permanently

# find script dir (repo root assumed to be one level up if script in project root)
SCRIPT_PATH="$(realpath "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
REPO_ROOT="$SCRIPT_DIR"   # if INSTALL.sh lives at repo root
# REPO_ROOT="$(realpath "$SCRIPT_DIR/..")" # adjust if INSTALL.sh in subdir

# Detect platform-specific install base
if [ "$(uname -s)" = "Darwin" ]; then
  AMCA_BASE="$HOME/Library/Application Support/amca"
else
  AMCA_BASE="${XDG_DATA_HOME:-$HOME/.local/share}/amca"
fi

BIN_DIR="$AMCA_BASE/bin"
SNAKES_SRC="$REPO_ROOT/amca_impl/snakes"
TEMPLATES_SRC="$REPO_ROOT/amca_impl/blueprints"
RUNNER_SRC_POSIX="$REPO_ROOT/amca_impl/amca_runner_posix.c"

echo "Repo root: $REPO_ROOT"
echo "Install base: $AMCA_BASE"
echo "Bin dir: $BIN_DIR"

# sanity checks
if [ ! -d "$SNAKES_SRC" ]; then
  echo "ERROR: snakes source directory not found: $SNAKES_SRC" >&2
  exit 2
fi

mkdir -p "$BIN_DIR"
mkdir -p "$AMCA_BASE"
mkdir -p "$AMCA_BASE/templates"

# Copy snakes dir
if command -v rsync >/dev/null 2>&1; then
  echo "Copying snakes/ -> $AMCA_BASE using rsync"
  rsync -a --delete "$SNAKES_SRC/" "$AMCA_BASE/snakes/"
else
  echo "Copying snakes/ -> $AMCA_BASE using cp -a"
  mkdir -p "$AMCA_BASE/snakes"
  cp -a "$SNAKES_SRC/." "$AMCA_BASE/snakes/"
fi

# compile runner (POSIX variant) if source exists
if [ -f "$RUNNER_SRC_POSIX" ]; then
  echo "Compiling POSIX runner..."
  if cc "$RUNNER_SRC_POSIX" -o "$BIN_DIR/amca"; then
    chmod +x "$BIN_DIR/amca"
    echo "Compiled runner -> $BIN_DIR/amca"
  else
    echo "Warning: failed to compile amca runner (cc returned non-zero)."
  fi
else
  echo "POSIX runner source not found at $RUNNER_SRC_POSIX; skipping compile."
fi

# install templates
if [ -d "$TEMPLATES_SRC" ]; then
  for d in "$TEMPLATES_SRC"/*; do
    [ -d "$d" ] || continue
    name="$(basename "$d")"
    echo "installing template: $name"
    if command -v rsync >/dev/null 2>&1; then
      rsync -a "$d/" "$AMCA_BASE/templates/$name/"
    else
      mkdir -p "$AMCA_BASE/templates/$name"
      cp -a "$d/." "$AMCA_BASE/templates/$name/"
    fi
  done
fi

# Add PATH persistently (marker block)
add_path_marker() {
  local profile="$1"
  local newdir="$2"
  local start_marker="# >>> amca PATH >>>"
  local end_marker="# <<< amca PATH <<<"

  mkdir -p "$(dirname "$profile")"
  touch "$profile"

  # remove existing block if present
  if grep -qF "$start_marker" "$profile"; then
    awk -v s="$start_marker" -v e="$end_marker" '
      $0==s {flag=1; next}
      $0==e {flag=0; next}
      flag==0 {print}
    ' "$profile" > "${profile}.tmp" && mv "${profile}.tmp" "$profile"
  fi

  # append new marker block
  cat >> "$profile" <<EOF

$start_marker
# Added by amca installer — do not remove unless you uninstall amca
if ! echo "\$PATH" | /bin/grep -q -E "(^|:)$newdir(:|$)"; then
  export PATH="\$PATH:$newdir"
fi
$end_marker

EOF
}

# Add universal alias permanently
add_alias_marker() {
  local profile="$1"
  local alias_name="$2"
  local alias_cmd="$3"
  local start_marker="# >>> amca ALIAS >>>"
  local end_marker="# <<< amca ALIAS <<<"

  mkdir -p "$(dirname "$profile")"
  touch "$profile"

  # Remove existing block if present
  if grep -qF "$start_marker" "$profile"; then
    awk -v s="$start_marker" -v e="$end_marker" '
      $0==s {flag=1; next}
      $0==e {flag=0; next}
      flag==0 {print}
    ' "$profile" > "${profile}.tmp" && mv "${profile}.tmp" "$profile"
  fi

  # Detect fish syntax
  if [[ "$(basename "$profile")" == "config.fish" ]]; then
    alias_line="alias $alias_name $alias_cmd"
  else
    alias_line="alias $alias_name='$alias_cmd'"
  fi

  # Append marker block
  cat >> "$profile" <<EOF

$start_marker
# Added by amca installer — do not remove unless you uninstall amca
$alias_line
$end_marker

EOF
}

# List of potential shell profiles
PROFILE_FILES=("$HOME/.profile" "$HOME/.bashrc" "$HOME/.zprofile" "$HOME/.zshrc" "$HOME/.config/fish/config.fish")

for pf in "${PROFILE_FILES[@]}"; do
  case "$(basename "$pf")" in
    config.fish)
      if ! grep -qF "$BIN_DIR" "$pf" 2>/dev/null; then
        echo "set -gx PATH \$PATH $BIN_DIR" >> "$pf"
        echo "Wrote PATH to $pf (fish syntax)."
      fi
      add_alias_marker "$pf" "amca" "xpath"
      break
      ;;
    *)
      if [ ! -f "$pf" ] || ! grep -qF "# >>> amca PATH >>>" "$pf" 2>/dev/null; then
        add_path_marker "$pf" "$BIN_DIR"
        add_alias_marker "$pf" "amca" "xpath"
        echo "Wrote amca PATH and ALIAS block to $pf"
        break
      fi
      ;;
  esac
done

echo ""
echo "Installation summary:"
echo " - snakes installed to: $AMCA_BASE/snakes"
echo " - templates installed to: $AMCA_BASE/templates"
echo " - runner installed to: $BIN_DIR/amca (if compiled)"
echo " - alias 'amca' -> 'xpath' added to shell profile"
echo ""
echo "What you need to do:"
echo "  Create an alias for $BIN_DIR/amca so you can easily call it from anywhere"
