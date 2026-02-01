#!/usr/bin/env python3
"""
Verify GitHub SSH keys in your known_hosts against official API.

This script checks if your known_hosts has the correct GitHub SSH keys
by comparing them with what GitHub publishes in their API.
"""

import json
import re
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

GITHUB_META_API = "https://api.github.com/meta"
GITHUB_DOMAINS = ["github.com", "ssh.github.com"]


def fetch_github_ssh_keys():
    """Fetch SSH public keys from GitHub's API."""
    try:
        req = Request(GITHUB_META_API, headers={'User-Agent': 'GitHubKnownHostsVerifier/1.0'})
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return set(data.get('ssh_keys', []))
    except (URLError, HTTPError) as e:
        print(f"❌ Error fetching GitHub SSH keys: {e}")
        return None


def parse_known_hosts(known_hosts_path):
    """Extract GitHub SSH keys from known_hosts."""
    if not known_hosts_path.exists():
        return {}
    
    github_keys = {domain: set() for domain in GITHUB_DOMAINS}
    github_pattern = re.compile(r'^(github\.com|ssh\.github\.com)(?:,|\s+)(.+)$')
    
    with open(known_hosts_path, 'r') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line or line.startswith('#'):
                continue
            
            match = github_pattern.match(line)
            if match:
                domain = match.group(1)
                key = match.group(2).strip()
                github_keys[domain].add(key)
    
    return github_keys


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Verify GitHub SSH keys in known_hosts against official API"
    )
    parser.add_argument(
        '--known-hosts',
        type=Path,
        default=Path.home() / '.ssh' / 'known_hosts',
        help='Path to known_hosts file (default: ~/.ssh/known_hosts)'
    )
    
    args = parser.parse_args()
    
    print("🔍 Checking GitHub SSH keys...")
    print()
    
    # Fetch official keys
    official_keys = fetch_github_ssh_keys()
    if official_keys is None:
        print("⚠️  Could not fetch keys from API. Cannot verify.")
        return 1
    
    print(f"📦 GitHub publishes {len(official_keys)} official SSH keys")
    
    # Parse local known_hosts
    local_keys = parse_known_hosts(args.known_hosts)
    
    if not any(local_keys.values()):
        print(f"❌ No GitHub keys found in {args.known_hosts}")
        print("   Run update_github_known_hosts.py to add them")
        return 1
    
    # Check each domain
    all_good = True
    for domain in GITHUB_DOMAINS:
        domain_keys = local_keys[domain]
        
        if not domain_keys:
            print(f"⚠️  {domain}: No keys found")
            all_good = False
            continue
        
        print(f"\n🔑 {domain}: {len(domain_keys)} keys")
        
        # Check if all local keys are official
        extra_keys = domain_keys - official_keys
        if extra_keys:
            print(f"   ⚠️  {len(extra_keys)} UNKNOWN keys (not in GitHub's official list)")
            all_good = False
        
        # Check if we have all official keys
        missing_keys = official_keys - domain_keys
        if missing_keys:
            print(f"   ⚠️  {len(missing_keys)} MISSING keys (published by GitHub)")
            all_good = False
        
        if not extra_keys and not missing_keys:
            print(f"   ✅ All keys match GitHub's official list")
    
    print()
    if all_good:
        print("✅ Your known_hosts is up to date with GitHub!")
        return 0
    else:
        print("⚠️  Your known_hosts needs updating")
        print("   Run: python3 update_github_known_hosts.py")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
