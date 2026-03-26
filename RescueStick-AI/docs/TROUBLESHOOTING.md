# RescueStick AI - Troubleshooting Guide

## Common Issues and Solutions

---

## Boot Issues

### Problem: USB doesn't boot

**Symptoms:**
- No boot menu appears
- System boots to Windows instead

**Solutions:**
1. Check boot order in BIOS (USB must be first)
2. Enable "Legacy Boot" if UEFI only
3. Try different USB port (USB 2.0 sometimes works better)
4. Re-write image with better tool (Rufus, Balena Etcher)

---

### Problem: Boot hangs at "Loading"

**Symptoms:**
- Boot menu works but system doesn't load

**Solutions:**
1. Check integrity of ISO/IMG
2. Verify all files copied correctly
3. Check available RAM (need 4GB minimum)
4. Try "nomodeset" kernel parameter

---

## Windows Mount Issues

### Problem: Can't see Windows partitions

**Symptoms:**
- "No Windows found" message
- Empty drive list

**Solutions:**
```bash
# List partitions
sudo fdisk -l

# Check NTFS
sudo ntfsfix /dev/sda1

# Mount manually
sudo mount -t ntfs-3g /dev/sda1 /mnt/windows
```

---

### Problem: "Read-only" errors

**Symptoms:**
- Can't write to Windows partition

**Solutions:**
1. Normal - RescueStick mounts read-only for safety
2. If need write access:
```bash
# Unmount then remount read-write
sudo umount /mnt/windows
sudo mount -t ntfs-3g /dev/sda1 /mnt/windows -o rw,uid=1000
```

---

## Diagnostic Issues

### Problem: Hash check fails on all files

**Symptoms:**
- "Hash mismatch" on every file
- False positives

**Solutions:**
1. Verify hash baseline matches Windows version exactly
2. Check baseline is for same Windows build
3. Ignore known-differences (user files, temp)
4. Update baselines for Windows updates

---

### Problem: Registry analysis finds too many issues

**Symptoms:**
- Thousands of "problems" reported

**Solutions:**
1. Normal - baseline comparison shows all differences
2. Focus on critical paths only (SYSTEM, SOFTWARE)
3. Filter out non-critical keys
4. Use Oracle engine for context

---

### Problem: Event logs show no errors

**Symptoms:**
- "No issues found" but system won't boot

**Solutions:**
1. Check logs on mounted Windows:
```bash
ls -la /mnt/windows/Windows/System32/winevt/Logs/
```
2. Try boot log location
3. Use bootrec /scanOS from Windows RE
4. Run manual disk check

---

## Repair Issues

### Problem: Repair fails

**Symptoms:**
- "Repair failed" messages
- No changes made

**Solutions:**
1. Check disk space on Windows partition
2. Verify file permissions
3. Check logs in `/rescue-stick/logs/`
4. Try individual repair (not full auto)

---

### Problem: System won't boot after repair

**Symptoms:**
- Repair succeeded but Windows won't start

**Solutions:**
1. Boot to Windows RE (Recovery Environment)
2. Run:
```
bootrec /fixmbr
bootrec /fixboot
bootrec /scanos
bootrec /rebuildbcd
```
3. Try System Restore
4. If all fails, suggest clean install

---

## Knowledge Base Issues

### Problem: Search returns no results

**Symptoms:**
- Empty search results

**Solutions:**
1. Rebuild search index
2. Add more articles
3. Try different keywords
4. Check index.db exists

---

### Problem: Articles missing

**Symptoms:**
- Links broken

**Solutions:**
- Add articles per KBA template in BUILD.md
- Populate kb/articles/ folder
- Each symptom should have corresponding article

---

## Performance Issues

### Problem: Scan takes too long

**Symptoms:**
- Full scan > 30 minutes

**Solutions:**
1. Use symptom-based scan (not full)
2. Check RAM - should be in tmpfs
3. Skip hash verification (faster but less thorough)
4. Limit to critical files only

---

### Problem: Out of memory

**Symptoms:**
- System crashes during scan

**Solutions:**
1. Close other applications
2. Use smaller scan scope
3. Add more RAM (8GB recommended)
4. Enable swap

---

## Data Issues

### Problem: Missing baselines

**Symptoms:**
- "No baseline for this Windows version"

**Solutions:**
1. Add baseline data to `/rescue-stick/data/`
2. Download from SOURCES.md sources
3. Build from clean install

---

### Problem: DLL cache empty

**Symptoms:**
- Missing DLL errors during repair

**Solutions:**
1. Pre-populate dll_cache folder
2. Use WinGet to download packages
3. Add common DLLs manually

---

## Quick Diagnostics

```bash
# Check system info
uname -a
free -h
df -h

# Check Windows
ls /mnt/windows/Windows/
sudo fdisk -l

# Check logs
tail -f /rescue-stick/logs/*.log

# Check engines
cd /rescue-stick/engines
python3 -c "import *; print('OK')"
```

---

## Getting Help

1. Check KB: Press H from main menu
2. Check logs: `/rescue-stick/logs/`
3. Run in verbose mode
4. Check GitHub issues

---

*Last Updated: 2026-03-26*