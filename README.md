<img src="https://raw.githubusercontent.com/geerlingguy/mac-dev-playbook/master/files/Mac-Dev-Playbook-Logo.png" width="250" height="156" alt="Mac Dev Playbook Logo" />

# Mac Development Ansible Playbook

[![CI][badge-gh-actions]][link-gh-actions]

This playbook installs and configures the software, tools, and macOS settings I use on my Mac for homelab management, DevOps, and general personal use. Some things in macOS are difficult to automate, so a few manual steps remain — but they're documented here.


## 🚀 Quick Start (Bootstrap)

This repository includes a bootstrap script to fully provision a new macOS machine with all required tools, applications, dotfiles, and system configuration.

### 1. Run bootstrap script

Execute the following command to provision your machine:

```bash
curl -sSL https://raw.githubusercontent.com/dazzathewiz/mac-dev-playbook/master/bootstrap.sh | bash
```

> You may be prompted to complete the Xcode Command Line Tools installation on first run. If so, re-run the bootstrap script afterwards.

---

### What the bootstrap does

The bootstrap script will:

- Install Xcode Command Line Tools (if required)
- Install Homebrew (if not already installed)
- Install Ansible
- Clone required repositories into `~/code/`
  - `dotfiles`
  - `mac-dev-playbook`
  - Additional configured repositories
- Install Ansible Galaxy dependencies

---

### 2. Run the Ansible playbook

The playbook is run separately to allow review before applying system changes.

On a fresh machine, Homebrew won't be in your shell PATH yet — run the `eval` first so `ansible-playbook` can be found:

Some casks use `.pkg` installers that call `sudo` internally. macOS ties cached sudo credentials to the TTY, so Ansible's subprocess can't reuse them — a known limitation discussed in [geerlingguy/mac-dev-playbook#53](https://github.com/geerlingguy/mac-dev-playbook/issues/53). Grant temporary passwordless sudo before running the playbook and remove it immediately after:

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
cd ~/code/mac-dev-playbook

# Grant temporary passwordless sudo for pkg-based cask installs
echo "$(whoami) ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/ansible-bootstrap

ansible-playbook main.yml -e @dazzathewiz.config.yml --ask-become-pass

# Remove passwordless sudo immediately after
sudo rm /etc/sudoers.d/ansible-bootstrap
```

> After the playbook installs your dotfiles, future terminal sessions will have Homebrew in PATH automatically.

---

### 3. Authenticate GitHub CLI

Once the playbook has installed `gh`, set up GitHub authentication so git operations work:

```bash
gh auth login
```

Alternatively, re-run the bootstrap script — it will detect `gh` is now installed and prompt for authentication automatically.

---

### Notes

- Some steps may require sudo privileges.
- Sign into the **Mac App Store** before running the playbook — `mas` requires an active App Store session to install apps.
- SSH keys and additional secure configuration are handled separately.
- OSX settings are handled by the `.osx` dotfile in the [dotfiles](https://github.com/dazzathewiz/dotfiles) repo.
- The bootstrap script assumes **Apple Silicon** (Homebrew at `/opt/homebrew`). It is not tested on Intel Macs.

---

## ⚙️ Manual Setup (Alternative)

If you prefer not to use the bootstrap script:

  1. Ensure Apple's command line tools are installed (`xcode-select --install` to launch the installer).
  2. [Install Ansible](https://docs.ansible.com/ansible/latest/installation_guide/index.html):

     1. Run the following command to add Python 3 to your $PATH: `export PATH="$HOME/Library/Python/3.9/bin:/opt/homebrew/bin:$PATH"`
     2. Upgrade Pip: `sudo pip3 install --upgrade pip`
     3. Install Ansible: `pip3 install ansible`

  3. Clone or download this repositories to your local drive:
     1. "https://github.com/dazzathewiz/mac-dev-playbook.git" "mac-dev-playbook"
     2. "https://github.com/dazzathewiz/dotfiles.git" "dotfiles"
  4. Run `ansible-galaxy install -r requirements.yml` inside this directory to install required Ansible roles.
  5. Run `ansible-playbook main.yml -e @dazzathewiz.config.yml --ask-become-pass` inside this directory. Enter your macOS account password when prompted for the 'BECOME' password.

> Note: If some Homebrew commands fail, you might need to agree to Xcode's license or fix some other Brew issue. Run `brew doctor` to see if this is the case.

---

## ✅ Post-Setup Checklist (Manual)

After running the playbook, optionally verify:

- Menu bar icons are arranged as desired
- VPN is configured and accessible
- Any required third-party apps are signed in
- Desktop / Spaces layout suits your workflow
- FileVault disk encryption is enabled (see below)
- Screen lock is set to **Immediately**: System Settings → Lock Screen → "Require password after screen saver begins or display is turned off"

> ⚠️ This is a personal macOS provisioning playbook tailored to my environment.  
> Some paths, applications, and repositories may need adjustment for other users.


## ⚠️ Not Managed by Ansible / `.osx`

The following macOS settings are **intentionally not automated**. These are either:

- user preference / low-value to codify
- brittle across macOS versions
- controlled by third-party apps
- or not reliably configurable via `defaults`

### 🔒 Screen Lock

The `.osx` dotfile attempts to set screen lock via `defaults write com.apple.screensaver askForPassword` but **macOS Sequoia no longer honours this setting** — it is silently overridden by System Settings.

The correct mechanism is `sysadminctl -screenLock immediate`, which requires admin privileges and is not yet wired into the `.osx` script as it needs further testing.

**Recommended approach:**
- Set manually: System Settings → Lock Screen → "Require password after screen saver begins or display is turned off" → **Immediately**

---

### 🔑 FileVault Disk Encryption

FileVault is **not automated** but should be enabled on first use of any machine.

**Reason:**
- Enabling FileVault requires generating a personal recovery key, which must be stored securely and cannot be handled non-interactively by a script
- Requires a reboot to complete encryption
- Running `fdesetup enable` in a playbook would require storing credentials in the repo

**Recommended approach:**
- Enable manually via System Settings → Privacy & Security → FileVault before or immediately after first run of the playbook
- Store the recovery key in 1Password

---

### 🍎 Menu Bar (Status Bar)

dotfiles `.osx` setting
Menu bar configuration is **not enforced**.

This includes:
- Visibility of system icons (Wi-Fi, Bluetooth, Battery, etc.)
- Ordering/position of icons
- Control Center modules (Focus, Now Playing, etc.)
- Third-party menu bar apps (e.g. VPN clients, utilities)

**Reason:**
- Apple does not provide stable automation interfaces
- Settings frequently change between macOS versions
- Third-party apps manage their own menu bar presence

**Recommended approach:**
- Configure manually via System Settings → Control Center
- Treat as personal preference

---

### 🔐 VPN Configuration

VPN setup is **not automated**.

This includes:
- VPN profiles (WireGuard, IPSec, etc.)
- Menu bar visibility for VPN
- Connection preferences

**Reason:**
- Credentials and secrets should not be stored in this repo
- VPN configuration is environment-specific
- Often managed by dedicated apps or MDM

**Recommended approach:**
- Configure manually or via the VPN client
- Ensure VPN menu bar icon is enabled if required

---

### 🧩 Third-Party Application Settings

Application-specific preferences are **not centrally managed**, including:

- Menu bar apps (e.g. 1Password, Tailscale, Rectangle)
- App-specific UI/UX preferences
- Login/startup behaviour (unless explicitly configured elsewhere)

**Reason:**
- Each app uses its own config mechanism
- Not all apps support CLI or idempotent configuration
- Better handled per-app if needed

---

### 🖥️ Desktop / Mission Control Layout

Not enforced:
- Number of desktops (Spaces)
- Assignment of apps to specific desktops
- Desktop wallpaper per Space

**Reason:**
- Highly personal workflow preference
- Dynamic by nature
- Not reliably scriptable

---

### ⌨️ Keyboard & Input Edge Cases

Not explicitly configured unless added manually:
- Key repeat rates
- Input sources / languages
- Modifier key remapping

**Reason:**
- Defaults are acceptable
- Preferences vary between users/devices

---

### 📸 Screenshot Location

dotfiles `.osx` setting.
Screenshot location is not set.

**Default behaviour:**
- Saves to Desktop

**Reason:**
- Low impact
- Easy to change if desired


## 🤖 Claude Desktop — GitHub MCP Server

The playbook provisions everything needed to run the [GitHub MCP server](https://github.com/github/github-mcp-server) for Claude Desktop, short of the secret itself:

- `github-mcp-server` is installed via Homebrew (`homebrew-core`, no tap required).
- A launch wrapper is installed to `~/.local/bin/github-mcp-claude`. It reads a GitHub PAT out of the macOS Keychain at launch and `exec`s the server — the token never sits in a config file or in this repo.
- The wrapper is registered as the `github` entry under `mcpServers` in `~/Library/Application Support/Claude/claude_desktop_config.json`, using its fully resolved absolute path — Claude Desktop does not expand `~` in `command`. This is a read-modify-write merge (`slurp` → `combine(recursive=True)` → `to_nice_json`), not a template — any other `mcpServers` entries and unrelated top-level keys (this file also holds live app state such as `coworkUserFilesPath` and browser allowlists, and Claude Desktop writes it routinely) are preserved. Confirmed by hand-testing, using the same read-merge-write shape this task automates, that this Claude Desktop version still honours a hand-edited `mcpServers` key.
- The write only happens when `mcpServers.github.command` doesn't already match the wrapper's path. Claude Desktop writes this file with 2-space indent in insertion order, while the merge's `to_nice_json` output is 4-space and alphabetised — comparing rendered bytes would make every run "changed" even with nothing to fix, and turn each run into a slurp-then-write-back race against the app. Once the `github` entry is correct, this task doesn't touch the file at all.

**Claude Desktop must be closed while the playbook runs** — the app also writes to this file, and a race between the two will clobber one side's changes. (The `command`-only convergence check above keeps steady-state runs from creating that race at all, but a run that actually needs to write — first-time setup, or the wrapper path changing — still writes the whole file.)

### One-time manual step: create the Keychain item (GitHub)

The PAT is a secret, and `security add-generic-password` is interactive, so it is deliberately **not** provisioned by the playbook. If it's missing when the wrapper runs, the wrapper prints the exact command instead of failing cryptically:

```bash
security add-generic-password -a "$USER" -s claude-github-mcp -w
```

Use a **classic** GitHub token with **`public_repo`** scope only.

If the tools don't appear, the JSON key is no longer honoured and the server likely needs registering as a `.mcpb` extension bundle via Settings → Extensions instead — which has no CLI path today, so it would stay a permanent manual step. Once this is confirmed either way, the playbook can be extended to automate registration too.

## 🤖 Claude Desktop — Proxmox MCP Server

The playbook provisions the Proxmox MCP server for Claude Desktop, short of the secret itself:

- `proxmox-mcp-server` is installed with `uv tool install proxmox-mcp-server[router]` (no Homebrew formula exists). Unpinned, same reasoning as the Homebrew packages above — `creates:` makes the install a no-op once present; upgrade deliberately with `uv tool upgrade proxmox-mcp-server`. The `[router]` extra collapses 200+ tool schemas down to 3 via semantic routing, at no security cost (`proxmox_api_raw` is in the full toolkit either way) but a large context saving per request.
- A launch wrapper is installed to `~/.local/bin/proxmox-mcp-claude`. It reads a Proxmox API token out of the macOS Keychain at launch and `exec`s the server.
- The wrapper is registered as the `proxmox` entry under `mcpServers`, using the same command-only, read-modify-write convergence check as the GitHub server above (see that section for why).

**This server has no read-only mode of its own** and exposes `proxmox_api_raw` (arbitrary API calls). The Keychain token is the *only* boundary — it must be a `claude-ro@pve` **PVEAuditor** token with privilege separation enabled, never `root@pam` (which is this server's own default). Verify the token 403s on a write before pointing anything at it.

`proxmox_mcp_host` is the node's FQDN, not its short name — the node carries a Let's Encrypt cert issued for the FQDN, which is what lets `PROXMOX_VERIFY_SSL` stay on with no CA bundle or Keychain import. This does pin the server to a single node.

### One-time manual step: create the Keychain item (Proxmox)

```bash
security add-generic-password -a "$USER" -s claude-proxmox-mcp -w
```

## 🤖 Claude Desktop — Unraid MCP Server

The playbook provisions the Unraid MCP server (via the Unraid Management Agent plugin) for Claude Desktop, short of the secret itself. Unlike the GitHub and Proxmox servers, **this one does not run on the Mac** — it runs on unNAS and speaks HTTP on `:8043`. Claude Desktop's config is stdio-only (`command`, never `url`), so [`mcp-remote`](https://www.npmjs.com/package/mcp-remote) runs locally as the stdio↔HTTP bridge:

- `node` (providing `npm`) and the global `mcp-remote` package are installed via `homebrew_installed_packages` / `npm_packages`. `mcp-remote` is called by its resolved absolute path rather than via `npx` — resolving the package at every launch overran Claude Desktop's startup window and surfaced as "Server disconnected".
- A launch wrapper is installed to `~/.local/bin/unraid-mcp-claude`. It reads a bearer token out of the macOS Keychain at launch and execs `mcp-remote` against `unraid_mcp_url` with `--allow-http`, which `mcp-remote` requires for a non-HTTPS URL.
- The wrapper is registered as the `unraid` entry under `mcpServers`, using the same command-only convergence check as the other two servers.

Read-only is enforced **on unNAS** (`READ_ONLY=true` in the plugin config), not by anything in this repo — a server-side flag rather than a scoped credential, weaker than the Proxmox server's PVEAuditor token. Re-test the refusal after any plugin update.

### One-time manual step: create the Keychain item (Unraid)

```bash
security add-generic-password -a "$USER" -s claude-unraid-mcp -w
```

## 🤖 Claude Desktop — Kubernetes MCP Server

The playbook provisions the [Kubernetes MCP server](https://github.com/containers/kubernetes-mcp-server) for the k3s cluster, short of the credential itself:

- `kubernetes-mcp-server` is installed via Homebrew (`homebrew-core`, a native Go binary), not `npx`. The npm package is a node shim: it needs `node` on PATH, which Claude Desktop doesn't provide, and it `console.log`s to stdout (the MCP channel) when it gets a signal. Resolving it at launch would also repeat the startup-window overrun that hit `mcp-remote`.
- A launch wrapper is installed to `~/.local/bin/kubernetes-mcp-claude`. It exports `KUBECONFIG` and passes `--kubeconfig`, both pointing at a scoped file (`~/.kube/mcp-view.config`, resolved to an absolute path at play time). It then `exec`s the server with `--read-only --disable-multi-cluster --toolsets core`.
- The wrapper is registered as the `kubernetes` entry under `mcpServers`, using the same command-only convergence check as the other three servers.

**Read-only is enforced in two independent layers**, unlike Proxmox, which relies on its token alone:

1. **Server.** `--read-only` exposes only tools annotated `readOnlyHint`. `--disable-multi-cluster` and `--toolsets core` remove the context and kubeconfig tools altogether.
2. **Credential.** The kubeconfig holds **exactly one context**: the `claude-mcp-view` ServiceAccount, bound to the built-in `view` ClusterRole plus a nodes-only read role. It's declared in the fluxcd repo (`infrastructure/configs/claude-mcp-view.yaml`). `view` excludes Secrets by design. The single context isn't tidiness. This server ships context-management tools, so if it could see the admin context, switching to it would be the escalation path, and that path never has to defeat `--read-only`. **Never point this at `~/.kube/config`, and never merge contexts into it.**

### One-time manual step: build the scoped kubeconfig (Kubernetes)

The token is a live credential, so the playbook deliberately **doesn't** build this file. It's a mode `0600` file, handled the same way as the admin kubeconfig rather than through Keychain. The playbook warns if the file is missing, and the wrapper refuses to start without it. Build it after the fluxcd ServiceAccount has reconciled, using your admin kubeconfig to *read* the token and the API endpoint:

```bash
SERVER="$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')"
TOKEN="$(kubectl -n mcp get secret claude-mcp-view-token -o jsonpath='{.data.token}' | base64 -d)"
CA="$(kubectl -n mcp get secret claude-mcp-view-token -o jsonpath='{.data.ca\.crt}')"
( umask 077; cat > ~/.kube/mcp-view.config <<EOF
apiVersion: v1
kind: Config
clusters:
- name: k3s
  cluster:
    server: ${SERVER}
    certificate-authority-data: ${CA}
users:
- name: claude-mcp-view
  user:
    token: ${TOKEN}
contexts:
- name: claude-mcp-view@k3s
  context: {cluster: k3s, user: claude-mcp-view}
current-context: claude-mcp-view@k3s
EOF
)
unset SERVER TOKEN CA
```

Then prove the credential layer on its own, before wiring anything up:

```bash
export KUBECONFIG=~/.kube/mcp-view.config
kubectl get nodes                                # succeeds
kubectl get secrets -A                           # Forbidden
kubectl -n <ns> scale deploy/<name> --replicas=1 # Forbidden
```

To rotate the token, delete the `claude-mcp-view-token` Secret. Flux recreates it with a fresh token. Then rebuild this file.

---

## Reconfiguring Settings

Refer to the [upstream geerlingguy/mac-dev-playbook README](https://github.com/geerlingguy/mac-dev-playbook) for advanced usage:

- Running against a remote Mac
- Running specific tagged tasks only
- Overriding default configuration values



## Included Applications / Configuration (Default)

Dock (pinned apps, in order):

  1. Mission Control
  2. Safari
  3. Messages
  4. Google Chrome
  5. System Settings
  6. 1Password
  7. App Store
  8. Terminal

Dock (removed):

  - Launchpad
  - Mail
  - Maps
  - Photos
  - FaceTime
  - Calendar
  - Contacts
  - Reminders
  - Notes
  - TV
  - Music
  - Games
  - iPhone Mirroring

Applications (installed with Homebrew Cask):

  - [1Password](https://1password.com/) + CLI
  - [Adobe Acrobat Reader](https://www.adobe.com/acrobat/pdf-reader.html)
  - [balenaEtcher](https://etcher.balena.io/)
  - [Citrix Workspace](https://www.citrix.com/products/receiver/)
  - [Discord](https://discord.com/)
  - [Dropbox](https://www.dropbox.com/)
  - [Google Chrome](https://www.google.com/chrome/)
  - [Home Assistant](https://www.home-assistant.io/)
  - [Lens](https://k8slens.dev/) (Kubernetes IDE)
  - [Logitech G Hub](https://www.logitechg.com/en-au/innovation/g-hub.html)
  - [macFUSE](https://macfuse.github.io/)
  - [Microsoft Office](https://www.microsoft.com/en-au/microsoft-365/mac/microsoft-365-for-mac)
  - [Microsoft Teams](https://www.microsoft.com/en-au/microsoft-teams/group-chat-software)
  - [Mos](https://mos.caldis.me/) (smooth scrolling)
  - [MQTT Explorer](https://mqtt-explorer.com/)
  - [Plex](https://www.plex.tv/)
  - [Slack](https://slack.com/)
  - [Spotify](https://www.spotify.com/)
  - [Visual Studio Code](https://code.visualstudio.com/)
  - [VLC](https://www.videolan.org/vlc/)
  - [Webex Meetings](https://www.webex.com/)
  - [Zoom](https://zoom.us/)

Packages (installed with Homebrew):

  - age
  - ansible
  - balena-cli
  - flux
  - gh
  - git
  - helm
  - kubernetes-cli
  - mas
  - sops
  - sshpass
  - starship
  - telnet
  - unar

Homebrew taps:

  - datreeio/datree
  - fluxcd/tap
  - hudochenkov/sshpass

My [dotfiles](https://github.com/dazzathewiz/dotfiles) are also installed into the current user's home directory, including the `.osx` dotfile for configuring many aspects of macOS for better performance and ease of use. You can disable dotfiles management by setting `configure_dotfiles: no` in your configuration.

Dotfiles installed:

  - `.zshrc`
  - `.gitconfig`
  - `.profile`
  - `.config/starship.toml`
  - `.osx`


## Author

This project was forked from the creator [Jeff Geerling](https://www.jeffgeerling.com/) (originally inspired by [MWGriffin/ansible-playbooks](https://github.com/MWGriffin/ansible-playbooks)).

