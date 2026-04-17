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

> ⚠️ This is a personal macOS provisioning playbook tailored to my environment.  
> Some paths, applications, and repositories may need adjustment for other users.


## ⚠️ Not Managed by Ansible / `.osx`

The following macOS settings are **intentionally not automated**. These are either:

- user preference / low-value to codify
- brittle across macOS versions
- controlled by third-party apps
- or not reliably configurable via `defaults`

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
  6. Google Chat

Dock (removed):

  - Launchpad
  - App Store
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
  - xkcdpass

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

