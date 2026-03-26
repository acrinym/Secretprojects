# RescueStick AI - Offline Data Sources

This document lists pre-bundled data sources for offline Windows repair - all MIT/GPL sources.

---

## 1. Core System Tools (Linux Base)

These tools are already open source and available in Linux repositories:

| Tool | Package | License | Purpose |
|------|---------|---------|---------|
| ntfs-3g | ntfs-3g | GPLv2 | Read/write NTFS |
| chntpw | chntpw | GPL | Registry editor |
| hivex | libhivex-dev | LGPL | Hive parsing |
| reglookup | reglookup | BSD | Registry search |
| sleuthkit | sleuthkit | CPL | File system analysis |
| testdisk | testdisk | GPL | Data recovery |
| photorec | photorec | GPL | File recovery |

**Install:**
```bash
# Debian/Ubuntu
sudo apt-get install ntfs-3g chntpw libhivex-bin reglookup sleuthkit testdisk
```

---

## 2. Vanilla Registry Baselines

### Primary Source: GitHub - AndrewRathbun/VanillaWindowsRegistryHives
**URL:** https://github.com/AndrewRathbun/VanillaWindowsRegistryHives
**License:** MIT
**Description:** Recursive dump of every Windows Registry hive from vanilla (clean) installs using KAPE

**Contains:**
- Windows 10 (all versions)
- Windows 11 (all versions)
- Windows Server (all versions)

**Usage:**
- Clone entire repo → extract hives for each OS version
- Compare against target system's registry
- Identify added/modified keys

**Files to download:**
```bash
# Clone the repo
git clone https://github.com/AndrewRathbun/VanillaWindowsRegistryHives.git

# Structure:
# Windows10/    → Windows 10 registry dumps
# Windows11/    → Windows 11 registry dumps
# WindowsServer/ → Windows Server registry dumps
```

---

## 2. GitHub Repair Tools (MIT/GPL)

### A. Windows Repair Tool (MIT)
**URL:** https://github.com/Mohabdo21/Windows-Repair-Tool
**License:** MIT
**Description:** Interactive menu-driven Windows system repair

**Features:**
- System Image Repair (DISM)
- Windows Update Repair
- SFC /scannow automation

### B. Windows Repair Script (MIT)
**URL:** https://github.com/kocken/WindowsRepairScript
**License:** MIT
**Description:** Repairs corrupt Windows OS files via SFC, DISM, CHKDSK

### C. WinRepairTool
**URL:** https://github.com/Javinator9889/WinRepairTool
**License:** Open source
**Description:** Windows application for solving common problems

**Features:**
- DISM with Windows Update source
- System File Checker (SFC)
- Offline mode (SFC + CHKDSK only)

### D. Windows Maintenance Tool
**URL:** https://github.com/ios12checker/Windows-Maintenance-Tool
**Description:** Batch script for one-click Windows repairs and optimizations

**Features:**
- SFC /scannow
- DISM commands
- Disk cleanup
- Service management

### E. Windows-11-Fix-Tweaks
**URL:** https://github.com/kubaam/Windows-11-Fix-Tweaks
**License:** MIT
**Description:** All-in-one Windows 11 fix and tweaks batch script

### F. FixIt
**URL:** https://github.com/Ec-25/FixIt
**License:** MIT
**Description:** Lightweight Windows optimization and repair tool

### G. WindowsVerifier
**URL:** https://github.com/JakeCarterDPM/WindowsVerifier
**Description:** Script that automates SFC /scannow and DISM repair

### H. FixWin
**URL:** https://github.com/Nozdormv/fixwin
**Description:** Windows fix commands collection

### I. DISMTools
**URL:** https://github.com/CodingWonders/DISMTools
**License:** Open source
**Description:** GUI front-end for DISM

### J. Reset Windows Update Tool (MIT)
**URL:** https://github.com/ManuelGil/Script-Reset-Windows-Update-Tool
**License:** MIT
**Description:** Reset Windows Update components

---

## 3. chntpw / Registry Tools

### A. Official chntpw
**URL:** https://github.com/minacle/chntpw
**License:** GPL
**Description:** Offline NT Password & Registry Editor

### B. Rescatux chntpw
**URL:** https://github.com/rescatux/chntpw
**License:** GPL
**Description:** Chntpw fork aimed at automatic interaction

---

## 4. File System & Recovery Tools

### A. NTFS-3G
**URL:** https://github.com/tuxera/ntfs-3g
**License:** GPLv2
**Description:** Read/write NTFS driver for Linux

### B. hivex (LGPL)
**URL:** https://github.com/libguestfs/hivex
**License:** LGPL v2.1
**Description:** Library for reading/writing Windows Registry hive files

### C. The Sleuth Kit
**URL:** https://github.com/sleuthkit/sleuthkit
**License:** CPL
**Description:** Forensic file system analysis

---

## 5. Microsoft Official Sources (for DISM/SFC)

### A. Windows Update (Online Source)
- Uses Windows Update servers
- `DISM /Online /Cleanup-Image /RestoreHealth`

### B. Windows Installation Media (Offline Source)
1. **Media Creation Tool**
   - Download from: https://www.microsoft.com/en-us/software-download/windows10
   - Create ISO or USB
   - Use as source: `DISM /Source:WIM /InstallPath:\sources`

2. **ISO File Extraction**
   - Extract install.wim from ISO
   - Use specific index: `DISM /Source:WIM:\install.wim:1 /RestoreHealth`

### C. Windows Server Deployment Image Servicing and Management (DISM)
**Docs:** https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/repair-a-windows-image

---

## 6. WinGet Package Repository

**URL:** https://github.com/microsoft/winget-cli
**License:** MIT

**Usage:**
- Pre-cache packages on USB
- Download .NET, VC++ runtimes, other components

**Common Package IDs:**
```bash
# .NET Runtimes
Microsoft.DotNet.Runtime.6
Microsoft.DotNet.Runtime.7
Microsoft.DotNet.Runtime.8
Microsoft.DotNet.AspNetCore.6
Microsoft.DotNet.AspNetCore.7
Microsoft.DotNet.AspNetCore.8

# VC++ Runtimes
Microsoft.VCRedist.x64.2015+
Microsoft.VCLibs.x64.14.0
Microsoft.VCLibs.x86.14.0

# Other
Microsoft.WindowsTerminal
```

---

## 7. DLL Sources

### A. dll-files.com
- Large DLL repository
- Check terms of service for commercial use

### B. Microsoft Update Catalog
- Official Microsoft files
- Search: https://www.catalog.update.microsoft.com/

### C. DLL Cache Pre-build
- Build from clean Windows VMs
- Store hashes in SQLite

---

## 8. USB Pre-load Checklist

To make RescueStick fully offline-capable:

```bash
# 1. Registry Baselines (~500MB)
/rescue-stick/data/registry_baselines/
├── Windows10/
│   ├── 21H1/
│   ├── 21H2/
│   └── 22H2/
├── Windows11/
│   ├── 22H2/
│   └── 23H2/
└── WindowsServer/
    ├── 2019/
    └── 2022/

# 2. File Hash Baselines (~GBs)
# Hash databases for each Windows version

# 3. Repair Tools Scripts
/rescue-stick/tools/
├── WindowsRepairScript/      # From GitHub
├── winrepair/               # From GitHub
└── maintenance-tool/        # From GitHub

# 4. WinGet Packages (~GBs)
/rescue-stick/data/package_cache/
├── dotnet-runtime-8/
├── vc-redist-2022/
└── (other common packages)

# 5. DLL Cache
/rescue-stick/data/dll_cache/
├── msvcp140.dll
├── vcruntime140.dll
└── (other common DLLs)
```

---

## 9. Tweaks Module (Separate)

As requested - separate module for Windows tweaks:

**Planned features:**
- Start menu tweaks
- Privacy settings
- Performance tuning
- UI customization
- Bloatware removal

**Integration with MSDT:**
- Tweaks can be applied during/after repair
- User choice - repair only vs repair + tweak

---

## Summary Table (MIT/GPL Open Source Only)

| Source | Type | License | Offline? |
|--------|------|---------|----------|
| VanillaWindowsRegistryHives | Registry baselines | MIT | ✅ Yes |
| Mohabdo21/Windows-Repair-Tool | Repair tool | MIT | ✅ Yes |
| kocken/WindowsRepairScript | Repair tool | MIT | ✅ Yes |
| ios12checker/Windows-Maintenance-Tool | Repair tool | MIT | ✅ Yes |
| kubaam/Windows-11-Fix-Tweaks | Tweaks | MIT | ✅ Yes |
| Ec-25/FixIt | Repair tool | MIT | ✅ Yes |
| Nozdormv/fixwin | Commands | Open | ✅ Yes |
| Javinator9889/WinRepairTool | Repair tool | Open | ✅ Yes |
| CodingWonders/DISMTools | DISM GUI | Open | ✅ Yes |
| tuxera/ntfs-3g | NTFS driver | GPLv2 | ✅ Yes |
| minacle/chntpw | Registry editor | GPL | ✅ Yes |
| libguestfs/hivex | Hive library | LGPL | ✅ Yes |
| sleuthkit/sleuthkit | FS analysis | CPL | ✅ Yes |
| microsoft/winget-cli | Package manager | MIT | ✅ Yes |

---

## Additional Resources

### Windows Repair Tools (GitHub)
- **Windows Repair Toolbox** - https://github.com/DrDonk/everything
- **System Utilities** - https://github.com/moonbuggy/maintenance
- **Win10 SE** - https://github.com/ChrisInTX/Win10SE

### Documentation
- Microsoft DISM: https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/
- Windows Registry: https://learn.microsoft.com/en-us/windows/win32/sysinfo/registry-hives
- NTFS-3G: https://www.tuxera.com/community/ntfs-3g-manual/

### Tools Reference
- chntpw: https://github.com/minacle/chntpw
- Hivex: https://github.com/libguestfs/hivex
- Testdisk/Photorec: https://www.cgsecurity.org/

---

*Last Updated: 2026-03-26*
*Sources verified for offline use*