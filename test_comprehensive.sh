#!/bin/bash
# Comprehensive test of the GitHub known_hosts updater

set -e

SCRIPT="./update_github_known_hosts.py"
TEST_DIR=$(mktemp -d)
TEST_KNOWN_HOSTS="$TEST_DIR/known_hosts"

echo "🧪 Running comprehensive tests..."
echo "Test directory: $TEST_DIR"
echo ""

# Test 1: Create a test known_hosts with mixed content
echo "=== Test 1: Creating test known_hosts ==="
cat > "$TEST_KNOWN_HOSTS" << 'EOF'
# Test known_hosts file
192.168.1.1 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDexamplekey...
example.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIExampleKeyData...

# Old GitHub entry (will be replaced)
github.com ssh-rsa AAAAB3NzaC1yc2EOLDKEY...

# Another host
bitbucket.org ssh-rsa AAAAB3NzaC1yc2EAAAABitbucketKey...
EOF

echo "Original known_hosts:"
cat "$TEST_KNOWN_HOSTS"
echo ""

# Test 2: Dry run
echo "=== Test 2: Dry run (preview changes) ==="
python3 "$SCRIPT" --known-hosts="$TEST_KNOWN_HOSTS" --use-fallback --dry-run
echo ""

# Test 3: Actual update
echo "=== Test 3: Actual update ==="
python3 "$SCRIPT" --known-hosts="$TEST_KNOWN_HOSTS" --use-fallback
echo ""

# Test 4: Verify the result
echo "=== Test 4: Verify updated known_hosts ==="
echo "File permissions:"
ls -l "$TEST_KNOWN_HOSTS"
echo ""

echo "Updated content:"
cat "$TEST_KNOWN_HOSTS"
echo ""

# Test 5: Count entries
echo "=== Test 5: Entry counts ==="
github_entries=$(grep -c "^github.com\|^ssh.github.com" "$TEST_KNOWN_HOSTS" || true)
other_entries=$(grep -v "^github.com\|^ssh.github.com\|^#\|^$" "$TEST_KNOWN_HOSTS" | wc -l || true)

echo "GitHub entries: $github_entries (expected: 6)"
echo "Other entries preserved: $other_entries (expected: 3)"
echo ""

# Test 6: Verify no duplicates
echo "=== Test 6: Check for duplicates ==="
duplicates=$(sort "$TEST_KNOWN_HOSTS" | uniq -d | wc -l)
if [ "$duplicates" -eq 0 ]; then
    echo "✅ No duplicate entries found"
else
    echo "❌ Found $duplicates duplicate entries"
fi
echo ""

# Test 7: Run again (idempotency test)
echo "=== Test 7: Idempotency test (run again) ==="
python3 "$SCRIPT" --known-hosts="$TEST_KNOWN_HOSTS" --use-fallback
entries_after_rerun=$(grep -c "^github.com\|^ssh.github.com" "$TEST_KNOWN_HOSTS" || true)
if [ "$entries_after_rerun" -eq "$github_entries" ]; then
    echo "✅ Entry count unchanged (idempotent)"
else
    echo "❌ Entry count changed: $github_entries → $entries_after_rerun"
fi
echo ""

# Cleanup
echo "=== Cleanup ==="
rm -rf "$TEST_DIR"
echo "✅ Test directory removed"
echo ""

echo "🎉 All tests completed!"
