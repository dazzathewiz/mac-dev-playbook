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
| `tasks/claude-mcp.yml` | Post-provision task: installs the GitHub MCP server's launch wrapper and registers it in Claude Desktop's config |
| `tasks/proxmox-mcp.yml` | Post-provision task: installs the Proxmox MCP server via `uv`, its launch wrapper, and registers it in Claude Desktop's config |
| `tasks/unraid-mcp.yml` | Post-provision task: installs the Unraid MCP server's launch wrapper (bridged over HTTP via `mcp-remote`) and registers it in Claude Desktop's config |
| `tasks/kubernetes-mcp.yml` | Post-provision task: installs the Kubernetes MCP server's launch wrapper (`--read-only`, scoped single-context kubeconfig) and registers it in Claude Desktop's config |

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
- **Add a post-provision task** → add a task file under `tasks/` and list it in `post_provision_tasks` in `dazzathewiz.config.yml`

## What Is Intentionally Not Automated

The following are documented in `README.md` and should not be added to the playbook:

- **FileVault** — requires interactive recovery key setup and a reboot
- **VPN** — credentials must not be stored in this repo
- **Menu bar layout** — no stable Apple automation interface
- **App Store sign-in** — must be done manually before running the playbook
- **SSH keys** — handled separately
- **GitHub PAT for the Claude MCP server** — a secret, and `security add-generic-password` is interactive; see README
- **Proxmox API token and Unraid bearer token for their MCP servers** — same reason; see README
- **The scoped kubeconfig for the Kubernetes MCP server** (`~/.kube/mcp-view.config`) — it embeds a live ServiceAccount token; see README. It must hold exactly one context (the `claude-mcp-view` SA, declared in the fluxcd repo), never the admin context: this server has context-switching tools, so a second context would bypass `--read-only`

## Conventions

- YAML files must pass `yamllint` and `ansible-lint` (enforced by CI)
- Inline YAML comments require 2 spaces before `#`
- The playbook is idempotent — changes should be safe to re-run
- This repo is Apple Silicon only (`bootstrap.sh` assumes Homebrew at `/opt/homebrew`)

## This repo is public

Comments, docs, commit messages and PR descriptions describe **mechanism**, generically: what a task does and how, which flags and patterns it relies on, and how to verify it. They do not describe the deployment behind it.

- **Keep out of public text:** IP addresses and network topology (subnets, VLANs, bind addresses, routing and VPN paths), certificate details, host and node inventories, and the dates or history of infrastructure changes.
- **Deliberate security trade-offs stay private.** Where a design accepts a risk on purpose (for example, how a credential travels or why a weaker control is acceptable), don't explain or justify it here. That reasoning is recorded in private project knowledge. At most, say the choice is deliberate.
- Values the playbook actually needs to run (a host name or URL in a `*_mcp_*` var) are fine. Commentary that explains what's behind them isn't.
- **Redact before the first push.** A later commit or a force-push doesn't remove text from GitHub: old commits stay reachable through PR timelines, and PR description edits keep their history. Grep the branch diff, the commit messages and the PR body before pushing, not after.
