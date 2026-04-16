# Mac Dev Playbook — Agent Context

This is a personal macOS provisioning repo for a homelab/DevOps setup. It uses Ansible to install applications, packages, and configure macOS settings on a fresh machine.

## Purpose

Automate the setup of a new Mac to a known-good state: applications, CLI tools, dotfiles, macOS system preferences, and Dock configuration. It is **not** a generic or shared playbook — it is tailored to a specific personal environment.

## Key Files

| File | Purpose |
|---|---|
| `bootstrap.sh` | First-run script for a fresh Mac. Installs Xcode CLT, Homebrew, Ansible, clones required repos. Does NOT run the playbook. |
| `main.yml` | Ansible playbook entry point |
| `dazzathewiz.config.yml` | Personal configuration — source of truth for what gets installed and configured |
| `default.config.yml` | Upstream defaults, overridden by `dazzathewiz.config.yml` |
| `requirements.yml` | Ansible Galaxy role dependencies |

## Workflow

The bootstrap and playbook are intentionally run as separate steps:

1. `bootstrap.sh` — sets up the minimum needed to run Ansible and clones repos
2. `ansible-playbook main.yml -e @dazzathewiz.config.yml --ask-become-pass` — run manually after reviewing
3. `gh auth login` — run after the playbook installs `gh`

## Making Changes

- **Add/remove applications or packages** → edit `dazzathewiz.config.yml`
- **Change macOS system preferences** → edit `dotfiles/.osx` (in the dotfiles repo)
- **Change Dock layout** → edit `dockitems_persist` / `dockitems_remove` in `dazzathewiz.config.yml`
- **Add Ansible roles or tasks** → edit `main.yml` and `requirements.yml`

## What Is Intentionally Not Automated

The following are documented in `README.md` and should not be added to the playbook:

- **FileVault** — requires interactive recovery key setup and a reboot
- **VPN** — credentials must not be stored in this repo
- **Menu bar layout** — no stable Apple automation interface
- **App Store sign-in** — must be done manually before running the playbook
- **SSH keys** — handled separately

## Conventions

- YAML files must pass `yamllint` and `ansible-lint` (enforced by CI)
- Inline YAML comments require 2 spaces before `#`
- The playbook is idempotent — changes should be safe to re-run
- This repo is Apple Silicon only (`bootstrap.sh` assumes Homebrew at `/opt/homebrew`)
