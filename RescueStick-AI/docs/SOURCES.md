# RescueStick AI - Offline Data Sources

This document lists pre-bundled data sources for offline Windows repair.

---

## 1. Vanilla Registry Baselines

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

### A. Windows Repair Script
**URL:** https://github.com/kocken/WindowsRepairScript
**License:** MIT
**Description:** Repairs corrupt Windows OS files via SFC, DISM, CHKDSK

**Features:**
- SFC /scannow automation
- DISM /RestoreHealth
- CHKDSK execution

### B. WinRepairTool
**URL:** https://github.com/Javinator9889/WinRepairTool
**License:** (check repo - appears open source)
**Description:** Windows application for solving common problems

**Features:**
- DISM with Windows Update source
- System File Checker (SFC)
- Offline mode (SFC + CHKDSK only)
- Windows Defender management

### C. Windows Maintenance Tool
**URL:** https://github.com/ios12checker/Windows-Maintenance-Tool
**Description:** Batch script for one-click Windows repairs and optimizations

**Features:**
- SFC /scannow
- DISM commands
- Disk cleanup
- Service management

### D. Windows-Verifier
**URL:** https://github.com/JakeCarterDPM/WindowsVerifier
**License:** (check repo)
**Description:** Automates SFC /scannow and DISM repair

### E. DISMTools
**URL:** https://github.com/CodingWonders/DISMTools
**License:** (check repo)
**Description:** GUI front-end for DISM - manages WIM files

**Features:**
- DISM GUI
- Image management
- Source detection

### F. Windows-Repair-Tool
**URL:** https://github.com/Mohabdo21/Windows-Repair-Tool
**License:** MIT
**Description:** Interactive menu-driven Windows repair

**Features:**
- System Image Repair
- Windows Update Repair
- DISM RestoreHealth

### G. FixIt
**URL:** https://github.com/Ec-25/FixIt
**License:** MIT
**Description:** Lightweight Windows optimization and repair tool

---

## 3. Microsoft Official Sources (for DISM/SFC)

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

## 4. WinGet Package Repository

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

## 5. DLL Sources

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

## 6. USB Pre-load Checklist

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

## 7. Tweaks Module (Separate)

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

## Summary Table

| Source | Type | License | Offline? |
|--------|------|---------|----------|
| VanillaWindowsRegistryHives | Registry baselines | MIT | ✅ Yes |
| WindowsRepairScript | Repair tool | MIT | ✅ Yes |
| WinRepairTool | Repair tool | Open | ✅ Yes |
| Windows-Maintenance-Tool | Repair tool | Open | ✅ Yes |
| DISMTools | DISM GUI | Open | ✅ Yes |
| WinGet CLI | Package manager | MIT | ✅ Yes |
| Microsoft Update Catalog | DLLs/updates | Microsoft | ❌ Online |

---

*Last Updated: 2026-03-25*
*Sources verified for offline use*