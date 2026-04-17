#!/bin/bash

CODE_DIR="$HOME/code"

ensure_repo() {
  local repo_url="$1"
  local repo_name="$2"
  local repo_path="$CODE_DIR/$repo_name"

  if [[ -d "$repo_path/.git" ]]; then
    echo "==> Repo already exists: $repo_name"
    git -C "$repo_path" remote -v
  else
    echo "==> Cloning $repo_name"
    git clone "$repo_url" "$repo_path"
  fi
}

# Install Xcode CLI tools if not present
if ! xcode-select -p &>/dev/null; then
  echo "Installing Xcode Command Line Tools..."
  xcode-select --install

  echo "Please complete installation, then re-run this script."
  exit 1
fi

# Install Homebrew if missing
if ! command -v brew &>/dev/null; then
  echo "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Install Ansible
if ! command -v ansible &>/dev/null; then
  echo "==> Installing Ansible
  brew install ansible
fi

echo "==> Ensuring code directory exists"
mkdir -p "$CODE_DIR"

# Required for bootstrap
ensure_repo "https://github.com/dazzathewiz/dotfiles.git" "dotfiles"
ensure_repo "https://github.com/dazzathewiz/mac-dev-playbook.git" "mac-dev-playbook"

# Regular working repos
ensure_repo "https://github.com/dazzathewiz/infrastructure.git" "infrastructure"
ensure_repo "https://github.com/dazzathewiz/fluxcd.git" "fluxcd"

# Install Ansible galaxy requirements
echo "==> Installing Ansible Galaxy requirements"
ansible-galaxy install -r "$CODE_DIR/mac-dev-playbook/requirements.yml"

# Run playbook after this bootstrap.
# ansible-playbook "$CODE_DIR/mac-dev-playbook/main.yml" -e "@$CODE_DIR/mac-dev-playbook/dazzathewiz.config.yml"

# Authenticate GitHub CLI if installed and not already authenticated
if command -v gh &>/dev/null && ! gh auth status &>/dev/null 2>&1; then
  echo "==> Authenticating GitHub CLI"
  gh auth login
fi