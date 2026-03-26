# RescueStick AI - Deployment Options

## Overview

RescueStick can be deployed in multiple ways:

1. **Standalone USB** - Complete bootable system
2. **Medicat Module** - Add to existing Medicat USB
3. **ISO/IMG** - Virtual or hardware deployment

---

## Option 1: Standalone USB

### Requirements
- USB drive: 32GB minimum (64GB recommended)
- System: x86_64 PC

### Build Steps
1. Follow BUILD.md
2. Configure GRUB bootloader
3. Copy to USB
4. Boot and test

### Pros
- Complete independence
- Full control over system
- No conflicts with other tools

### Cons
- Must build from scratch
- No integration with other tools

---

## Option 2: Medicat Integration

### Why Medicat?

**Medicat** is a popular bootable USB toolkit with:
- Multi-ISO support (100+ tools)
- Windows PE environment
- Useful for:
  - Anti-virus rescue disks
  - System repair tools
  - Partition management
  - Data recovery

### Integration Method

```bash
# Method 1: ISO with Easy2Boot
# Place RescueStick.iso in /Easy2Boot/Collection/
# Works with most ISOs

# Method 2: Direct files
/rescue-stick/
├── rescueStick/          # Main directory on Medicat USB
│   ├── vmlinuz          # Kernel
│   ├── initrd.img       # Initramfs
│   ├── rescue-stick/    # Application files
│   └── isolinux.cfg     # Boot config
└── tools/               # Portable tools folder
```

### Boot Entry (Medicat)
```cfg
LABEL RescueStick AI
  MENU LABEL RescueStick AI - Windows Repair
  KERNEL /rescue-stick/rescueStick/vmlinuz
  APPEND initrd=/rescue-stick/rescueStick/initrd.img boot=live config components
```

### Pros
- Already have multi-boot handled
- Includes additional tools
- Familiar workflow for Medicat users
- Single USB for everything

### Cons
- Medicat requirements
- Less control over RescueStick environment
- Potential conflicts

---

## Option 3: ISO/IMG for Virtualization

### Use Cases
- Remote repair (send ISO to client)
- VM-based recovery
- Testing before physical deployment

### Formats
- **ISO** - For CD/DVD/VM
- **IMG** - Direct USB write

### Tools
```bash
# Create ISO
genisoimage -o rescue-stick.iso -b isolinux/isolinux.bin \
    -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 \
    -boot-info-table rescue-stick/

# Create IMG
dd if=rescue-stick.iso of=rescue-stick.img bs=4M status=progress
```

---

## Medicat + RescueStick Combo

### Recommended Setup

```
Medicat USB/
├── [Boot Files]           # Medicat's boot infrastructure
├── RescueStick/           # RescueStick AI
│   ├── vmlinuz
│   ├── initrd.img
│   ├── rescue-stick/      # App files
│   ├── kb/                # Knowledge base
│   └── data/              # Baselines, caches
├── Tools/                 # Medicat's tools folder
│   ├── Antivirus/
│   ├── Partition/
│   ├── Recovery/
│   └── ...plus RescueStick tools
└── ISOs/                  # Additional ISOs
```

### Boot Menu Integration

When user boots Medicat:
```
┌────────────────────────────────────────┐
│           MEDICAT MAIN MENU            │
├────────────────────────────────────────┤
│ 1. Windows PE                         │
│ 2. Antivirus                          │
│ 3. Partition Tools                    │
│ 4. Recovery Tools                     │
│ 5. System Repair                      │
│                                        │
│ 6. >>> RESCUE STICK AI <<<            │
│    - AI Windows Diagnostics           │
│    - Symptom-based repair              │
│    - Knowledge base                    │
│                                        │
│ 7. More Tools...                      │
└────────────────────────────────────────┘
```

---

## Recommended Deployment

**For most users: Medicat Integration**

Reasons:
1. Medicat handles boot complexity
2. Already includes useful tools
3. Single USB solution
4. Industry standard

**For advanced users: Standalone USB**

Reasons:
1. Full control
2. Can customize everything
3. No Medicat dependencies

---

## Verification Checklist

- [ ] Boot menu shows RescueStick option
- [ ] Linux loads in RAM
- [ ] Tools accessible
- [ ] Windows partition mounts (read-only)
- [ ] Diagnostic menu works
- [ ] Knowledge base searchable
- [ ] All 10 engines load

---

*Last Updated: 2026-03-26*