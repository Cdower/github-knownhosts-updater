# GitHub Known Hosts Updater

A Python script to automatically update your SSH `known_hosts` file with GitHub's official SSH keys.

## Why?

When you use SSH to connect to GitHub (`git@github.com`), your computer verifies GitHub's identity using SSH keys stored in `~/.ssh/known_hosts`. This script ensures you always have the latest official keys from GitHub's API.

## Features

- ✅ Fetches current SSH keys from GitHub's public API
- ✅ Automatic fallback to cached keys if network unavailable
- ✅ Preserves non-GitHub entries in your known_hosts
- ✅ Atomic file writes (safe, no partial updates)
- ✅ Dry-run mode to preview changes
- ✅ No external dependencies (pure Python stdlib)

## Installation

Just download the script:

```bash
curl -O https://raw.githubusercontent.com/yourusername/github-known-hosts-updater/main/update_github_known_hosts.py
chmod +x update_github_known_hosts.py
```

Or clone the repo:

```bash
git clone https://github.com/yourusername/github-known-hosts-updater.git
cd github-known-hosts-updater
```

## Usage

### Update known_hosts:
```bash
python3 update_github_known_hosts.py
```

### Preview changes without modifying anything:
```bash
python3 update_github_known_hosts.py --dry-run
```

### Use cached keys without trying API:
```bash
python3 update_github_known_hosts.py --use-fallback
```

### Specify custom known_hosts location:
```bash
python3 update_github_known_hosts.py --known-hosts=/custom/path/known_hosts
```

## How It Works

1. Fetches SSH keys from `https://api.github.com/meta`
2. Falls back to cached keys if network unavailable
3. Parses your existing `~/.ssh/known_hosts`
4. Removes old GitHub entries
5. Adds current GitHub keys for both `github.com` and `ssh.github.com`
6. Preserves all non-GitHub entries
7. Writes atomically with proper permissions (0600)

## Requirements

- Python 3.6+
- No external dependencies

## Automation

Run automatically with cron:

```bash
# Update GitHub SSH keys daily at 3am
0 3 * * * /path/to/update_github_known_hosts.py
```

Or systemd timer:

```ini
# /etc/systemd/system/github-known-hosts.service
[Unit]
Description=Update GitHub SSH known_hosts

[Service]
Type=oneshot
ExecStart=/usr/local/bin/update_github_known_hosts.py

# /etc/systemd/system/github-known-hosts.timer
[Unit]
Description=Update GitHub SSH known_hosts daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

## Safety

- Uses atomic file writes (temp file + rename)
- Sets proper permissions (0600) before moving
- Dry-run mode to preview changes
- Preserves non-GitHub entries
- Graceful fallback if API unavailable

## Documentation

- **README.md** (this file): Quick reference
- **how-it-works.md**: Deep dive into architecture, decisions, and lessons learned

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or PR.

## Related Links

- [GitHub Meta API](https://api.github.com/meta)
- [GitHub's SSH Key Fingerprints](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints)
