# RescueStick AI - Build Guide

This document covers how to build the complete RescueStick USB system.

---

## Overview

RescueStick can be built in two ways:
1. **Standalone USB** - Self-contained bootable system
2. **Medicat Module** - Add to existing Medicat USB

---

## Part 1: Build Linux Live System

### Option A: Standalone USB

#### Step 1: Base System
```bash
# Use Debian netinst or Ubuntu Server
# Minimal install, no desktop needed

# Recommended: Debian 12 (Bookworm) amd64
wget https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-12.x.x-amd64-netinst.iso
```

#### Step 2: Add RescueStick Files
```bash
# Copy project files to USB
cp -r RescueStick-AI /path/to/usb/

# Structure:
/rescue-stick/
├── ai_core/           # AI diagnostic engine
├── engines/           # 10 holographic engines
├── kb/                # Knowledge base (to be populated)
├── tools/             # Windows repair tools
├── data/              # Hash baselines, caches
└── scripts/           # Build scripts
```

#### Step 3: Install Dependencies
```bash
# System packages
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip \
    ntfs-3g chntpw libhivex-bin \
    sqlite3 \
    # Add more from ENGINES.md
```

#### Step 4: Configure Boot
```bash
# Add GRUB entry for RescueStick
# /etc/grub.d/40_custom or similar
menuentry 'RescueStick AI' {
    set root='(hd0,1)'
    linux /rescue-stick/vmlinuz boot=live config components
    initrd /rescue-stick/initrd.img
}
```

### Option B: Medicat Integration

```bash
# Copy RescueStick to Medicat USB
# Medicat already handles multi-boot

/rescue-stick/
├── rescueStick.ai.iso      # Bootable image
├── rescueStick/            # Support files
└── tools/                  # Portable tools
```

---

## Part 2: Pre-load Data

### Required Data Files

```bash
# 1. File Hash Baselines (~GBs)
mkdir -p data/hash_baselines/
# Populate with:
# - Windows 10 21H1, 21H2, 22H2 hashes
# - Windows 11 22H2, 23H2 hashes
# - Windows Server 2019, 2022 hashes

# 2. Registry Baselines
mkdir -p data/registry_baselines/
# Clone: https://github.com/AndrewRathbun/VanillaWindowsRegistryHives

# 3. DLL Cache
mkdir -p data/dll_cache/
# Common DLLs: msvcp140.dll, vcruntime140.dll, etc.

# 4. WinGet Packages (optional)
mkdir -p data/package_cache/
# Pre-download common packages
```

---

## Part 3: Build ISO/IMG

### Using Cubic (Recommended)

```bash
# Install Cubic
sudo apt-add-repository ppa:cubic-wizard/release
sudo apt-get update
sudo apt-get install cubic

# Run Cubic
cubic
```

**Cubic Settings:**
- ISO name: RescueStick-AI
- Volume ID: RESCUE-STICK-AI
- Boot: GRUB2
- Preseed: custom (skip prompts)

### Manual Build

```bash
# Create ISO
xorriso -as mkisofs \
    -iso-level 3 \
    -joliet \
    -label "RescueStick-AI" \
    -volid "RescueStick-AI" \
    -output rescue-stick.iso \
    -boot-image isolinux.bin \
    -boot-info-table \
    -boot-load-size 4 \
    /path/to/rescue-stick/files/

# Create IMG (for USB)
dd if=rescue-stick.iso of=/dev/sdX bs=4M status=progress
```

---

## Part 4: Populate Knowledge Base

### KBA Structure
```bash
/kb/
├── index.db           # SQLite full-text search
├── articles/
│   ├── boot/
│   │   ├── 001-system-wont-boot.md
│   │   ├── 002-bsod-errors.md
│   │   └── ...
│   ├── updates/
│   ├── dlls/
│   ├── registry/
│   └── performance/
└── tools/
    ├── diagnostic-tools.md
    └── repair-tools.md
```

### KBA Template
```markdown
# Article Title

## Symptom
What the user sees

## Cause
Why it happens

## Fix
Step-by-step repair

## Verification
How to confirm it worked

## Related Tools
- Tool 1
- Tool 2

## Prevention
How to avoid recurrence
```

---

## Part 5: Testing

### VM Testing (Recommended First)
```bash
# Using QEMU
qemu-system-x86_64 \
    -m 4G \
    -cdrom rescue-stick.iso \
    -boot d \
    -hda test-disk.img
```

### Hardware Testing
```bash
# Write to test USB
sudo dd if=rescue-stick.img of=/dev/sdX bs=4M status=progress

# Boot and verify:
# - Linux loads in RAM
# - Tools accessible
# - Windows mount works
# - Diagnostic menu works
```

---

## Build Checklist

- [ ] Base Linux system
- [ ] Python dependencies
- [ ] Windows tools (chntpw, DISM, etc.)
- [ ] Hash baselines (all Windows versions)
- [ ] Registry baselines
- [ ] DLL cache
- [ ] Knowledge base articles
- [ ] Boot configuration (GRUB/Syslinux)
- [ ] ISO/IMG build
- [ ] VM test
- [ ] Hardware test

---

## Quick Start (Developer Build)

```bash
# Minimal build for development
cd /path/to/RescueStick-AI

# Create directory structure
mkdir -p data/hash_baselines data/registry_baselines data/dll_cache
mkdir -p kb/articles/boot kb/tools

# Test run (no boot needed)
python3 -c "from engines import *; print('Engines loaded')"
```

---

*Last Updated: 2026-03-26*