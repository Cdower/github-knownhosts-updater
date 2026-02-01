#!/usr/bin/env python3
"""
Update GitHub SSH known_hosts entries from official API.

This script fetches GitHub's current SSH key fingerprints from their public API
and updates your ~/.ssh/known_hosts file to match. This ensures you're always
using GitHub's official, current SSH keys.
"""

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# GitHub's public API endpoint for SSH keys
GITHUB_META_API = "https://api.github.com/meta"

# GitHub domains to manage in known_hosts
GITHUB_DOMAINS = ["github.com", "ssh.github.com"]

# Fallback SSH keys (from API as of 2025-02-01) in case network is unavailable
FALLBACK_SSH_KEYS = [
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl",
    "ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBEmKSENjQEezOmxkZMy7opKgwFB9nkt5YRrYMjNuG5N87uRgg6CLrbo5wAdT/y6v0mKV0U2w0WZ2YB/++Tpockg=",
    "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCj7ndNxQowgcQnjshcLrqPEiiphnt+VTTvDP6mHBL9j1aNUkY4Ue1gvwnGLVlOhGeYrnZaMgRK6+PKCUXaDbC7qtbW8gIkhL7aGCsOr/C56SJMy/BCZfxd1nWzAOxSDPgVsmerOBYfNqltV9/hWCqBywINIR+5dIg6JTJ72pcEpEjcYgXkE2YEFXV1JHnsKgbLWNlhScqb2UmyRkQyytRLtL+38TGxkxCflmO+5Z8CSSNY7GidjMIZ7Q4zMjA2n1nGrlTDkzwDCsw+wqFPGQA179cnfGWOWRVruj16z6XyvxvjJwbz0wQZ75XK5tKSb7FNyeIEs4TT4jk+S4dhPeAUC5y+bDYirYgM4GC7uEnztnZyaVWQ7B381AK4Qdrwt51ZqExKbQpTUNn+EjqoTwvqNj4kqx5QUCI0ThS/YkOxJCXmPUWZbhjpCg56i+2aB6CmK2JGhn57K5mj0MNdBXA4/WnwH6XoPWJzK5Nyu2zB3nAZp+S5hpQs+p1vN1/wsjk="
]


def fetch_github_ssh_keys(use_fallback=False):
    """Fetch SSH public keys from GitHub's API or use fallback data."""
    if use_fallback:
        print("📦 Using fallback SSH keys (API fetch skipped)")
        return FALLBACK_SSH_KEYS
    
    try:
        # Add a User-Agent header (GitHub API prefers this)
        req = Request(GITHUB_META_API, headers={'User-Agent': 'GitHubKnownHostsUpdater/1.0'})
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('ssh_keys', [])
    except (URLError, HTTPError) as e:
        print(f"⚠️  Network error fetching GitHub SSH keys: {e}", file=sys.stderr)
        print("   Using fallback keys instead (current as of 2025-02-01)", file=sys.stderr)
        return FALLBACK_SSH_KEYS
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing API response: {e}", file=sys.stderr)
        sys.exit(1)


def parse_known_hosts(known_hosts_path):
    """
    Parse the known_hosts file and return non-GitHub entries.
    
    Returns a list of lines that don't belong to GitHub domains.
    """
    if not known_hosts_path.exists():
        return []
    
    non_github_lines = []
    github_pattern = re.compile(r'^(github\.com|ssh\.github\.com)(,|\ )')
    
    with open(known_hosts_path, 'r') as f:
        for line in f:
            line = line.rstrip('\n')
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            # Keep non-GitHub entries
            if not github_pattern.match(line):
                non_github_lines.append(line)
    
    return non_github_lines


def format_known_hosts_entry(domain, key):
    """Format a single known_hosts entry."""
    return f"{domain} {key}"


def update_known_hosts(known_hosts_path, ssh_keys, dry_run=False):
    """
    Update the known_hosts file with current GitHub SSH keys.
    
    This removes old GitHub entries and adds fresh ones from the API.
    """
    # Ensure .ssh directory exists
    ssh_dir = known_hosts_path.parent
    if not dry_run:
        ssh_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    
    # Parse existing file, keeping non-GitHub entries
    existing_entries = parse_known_hosts(known_hosts_path)
    
    # Build new GitHub entries
    new_github_entries = []
    for domain in GITHUB_DOMAINS:
        for key in ssh_keys:
            new_github_entries.append(format_known_hosts_entry(domain, key))
    
    if dry_run:
        print("🔍 DRY RUN - No changes will be made\n")
        print("Would remove all existing GitHub entries")
        print(f"Would add {len(new_github_entries)} new GitHub entries:")
        for entry in new_github_entries:
            print(f"  {entry}")
        return
    
    # Write atomically using a temporary file
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=ssh_dir,
            delete=False,
            prefix='.known_hosts.tmp'
        ) as tmp_file:
            tmp_path = Path(tmp_file.name)
            
            # Write header
            tmp_file.write("# SSH known_hosts file\n")
            tmp_file.write("# GitHub entries updated by update_github_known_hosts.py\n\n")
            
            # Write GitHub entries
            if new_github_entries:
                tmp_file.write("# GitHub.com SSH keys\n")
                for entry in new_github_entries:
                    tmp_file.write(f"{entry}\n")
                tmp_file.write("\n")
            
            # Write other entries
            if existing_entries:
                tmp_file.write("# Other hosts\n")
                for entry in existing_entries:
                    tmp_file.write(f"{entry}\n")
        
        # Set proper permissions before moving
        tmp_path.chmod(0o600)
        
        # Atomic rename
        tmp_path.replace(known_hosts_path)
        
        print(f"✅ Updated {known_hosts_path}")
        print(f"   Added {len(new_github_entries)} GitHub entries")
        print(f"   Preserved {len(existing_entries)} other entries")
        
    except Exception as e:
        # Clean up temp file on error
        if tmp_path.exists():
            tmp_path.unlink()
        print(f"❌ Error writing known_hosts: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Update GitHub SSH keys in known_hosts from official API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Update known_hosts (tries API, falls back to cached keys)
  %(prog)s --use-fallback     # Use cached keys without trying API
  %(prog)s --dry-run          # Show what would change
  %(prog)s --known-hosts=/custom/path/known_hosts
        """
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--known-hosts',
        type=Path,
        default=Path.home() / '.ssh' / 'known_hosts',
        help='Path to known_hosts file (default: ~/.ssh/known_hosts)'
    )
    parser.add_argument(
        '--use-fallback',
        action='store_true',
        help='Use fallback keys without trying to fetch from API (useful in restricted networks)'
    )
    
    args = parser.parse_args()
    
    if not args.use_fallback:
        print("🔑 Fetching GitHub SSH keys from API...")
    ssh_keys = fetch_github_ssh_keys(use_fallback=args.use_fallback)
    
    if not ssh_keys:
        print("⚠️  No SSH keys found in API response", file=sys.stderr)
        sys.exit(1)
    
    print(f"📦 Retrieved {len(ssh_keys)} SSH keys from GitHub")
    
    update_known_hosts(args.known_hosts, ssh_keys, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
