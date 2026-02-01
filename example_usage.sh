#!/bin/bash
# Example usage scenarios for update_github_known_hosts.py

echo "=== Example 1: First-time usage with dry-run ==="
echo "This shows what the script would do without making changes"
echo "Command: python3 update_github_known_hosts.py --dry-run"
echo ""

echo "=== Example 2: Actual update ==="
echo "Command: python3 update_github_known_hosts.py"
echo ""

echo "=== Example 3: Using fallback keys (offline mode) ==="
echo "Command: python3 update_github_known_hosts.py --use-fallback"
echo ""

echo "=== Example 4: Custom known_hosts location ==="
echo "Command: python3 update_github_known_hosts.py --known-hosts=/tmp/test_known_hosts"
echo ""

echo "=== Example 5: Check what domains will be managed ==="
python3 update_github_known_hosts.py --help | grep -A 5 "Examples:"
