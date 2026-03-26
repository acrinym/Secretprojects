# RescueStick AI - Specification Document

## Project Overview

**Project Name:** RescueStick AI  
**Type:** Live USB Recovery Operating System with AI-Assisted Diagnostics  
**Core Functionality:** A bootable USB application that diagnoses and repairs Windows (and optionally Linux) systems using AI analysis, without requiring OS reinstallation.  
**Target Users:** IT professionals, system administrators, home users needing Windows repair without data loss.

---

## 1. Core Architecture

### 1.1 Platform
- **Primary OS:** Linux (preferred for flexibility and open-source nature)
- **Secondary OS:** Windows (fallback)
- **Boot Media:** USB flash drive (minimum 32GB recommended)
- **Execution Environment:** Runs entirely in RAM (Tmpfs) for maximum speed

### 1.2 System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        RESCUE STICK AI                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   BOOT      │  │   AI CORE   │  │  DIAGNOSTIC  │             │
│  │   LOADER    │  │   ENGINE    │  │   MODULES   │             │
│  │ (GRUB/Syslinux)│ (Python/AI) │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   WINDOWS   │  │   NETWORK   │  │   MSDT      │             │
│  │   ANALYZER  │  │   MODULE    │  │   INTEGRATION│             │
│  │             │  │             │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    STORAGE LAYERS                        │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │   │
│  │  │ RAMDisk │  │ USB     │  │ Target  │  │ Network │   │   │
│  │  │ (Tmpfs) │  │ Storage │  │ Mount   │  │ Cache   │   │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Feature Specifications

### 2.1 Windows Diagnostics Module

#### 2.1.1 File Inventory System
- **Hash Calculation:** SHA256, MD5 for all system files
- **File Location Tracking:** 
  - System32/SysWOW64
  - Program Files / Program Files (x86)
  - Windows/System32/Config
  - WinSxS
  - Catroot/Catroot2
  - DriverStore
  - ServicePackCache
- **Integrity Verification:** Compare against Microsoft baseline databases

#### 2.1.2 Registry Analysis
- **Hive Types:**
  - SYSTEM (HKLM\SYSTEM)
  - SOFTWARE (HKLM\SOFTWARE)
  - SECURITY (HKLM\SECURITY)
  - SAM (HKLM\SAM)
  - DEFAULT
  - USRCLASS.DAT (HKCU)
- **Analysis Areas:**
  - CurrentControlSet identification
  - Boot configuration (BCD)
  - Service configurations
  - Driver load order
  - Startup entries
  - File associations

#### 2.1.3 Application Data Analysis
- **Paths:**
  - %APPDATA% (Roaming)
  - %LOCALAPPDATA%
  - %PROGRAMDATA%
- **Analysis:**
  - Application crash logs
  - Windows Error Reporting artifacts
  - Update cache
  - Temp files corruption detection
  - Browser profile integrity

### 2.2 AI Core Engine

#### 2.2.1 Diagnostic Engine
- **Input Processing:**
  - Hash databases (local + cloud)
  - File system snapshots
  - Registry state capture
  - Event log analysis
  - Memory dump analysis (when available)
  
- **AI Analysis Pipeline:**
  1. Data normalization
  2. Anomaly detection (unsupported/corrupted files)
  3. Root cause analysis
  4. Repair strategy generation
  5. Risk assessment

#### 2.2.2 Adaptive Confidence System
Inspired by Synoptic Executive's adaptive threshold approach:

```python
class RepairDecisionEngine:
    def calculate_repair_confidence(self, issues, system_state):
        """
        Adaptive confidence based on:
        - Issue severity (corrupted vs missing vs modified)
        - Source availability (local cache vs network)
        - Risk assessment (system-critical vs optional)
        """
        base_confidence = 0.7
        
        # Low source availability? Be more conservative
        if not system_state.has_local_cache:
            base_confidence -= 0.2
        
        # System-critical file? Higher bar
        if issues.affects_boot:
            base_confidence += 0.1
            
        # Known pattern match? Higher confidence
        if issues.matches_known_pattern:
            base_confidence += 0.15
            
        return min(base_confidence, 0.95)
```

#### 2.2.3 Pattern Taxonomy System
Cross-domain pattern matching from Synoptic Executive:
- Map Windows error codes → registry issues → file corruption patterns
- Track repair outcomes → improve confidence over time
- Learn from each repair session

#### 2.2.4 Decision Matrix
- **File Missing:** Download from Microsoft Update/DISM source
- **File Corrupted:** Replace with verified hash from local/cloud database
- **Registry Broken:** Restore from backup or rebuild affected keys
- **System Corrupted:** Offer in-place upgrade via MSDT
- **Critical Failure:** Recommend clean install with data backup guidance

### 2.3 Repair Capabilities

#### 2.3.1 File-Level Repair
- Automatic file replacement using DISM
- Manual file injection for specific fixes
- DLL registration repair
- System file checker (SFC) automation

#### 2.3.2 Registry Repair
- Backup before any modification
- Selective key restoration
- Permission fixes
- Mounted hive repair

#### 2.3.3 Windows Update Repair
- Component Store cleanup (WinSXS)
- Update database rebuild
- CBS.log analysis and repair
- Automatic update service reconfiguration

#### 2.3.4 Boot Repair
- BCD rebuild
- Boot sector repair
- Startup environment repair
- Safe mode enablement

### 2.4 Network Capabilities

#### 2.4.1 Microsoft Source Integration
- Windows Update API access
- DISM online source
- Microsoft Catalog integration
- Media Creation Tool integration (offline)
- **WinGet (Windows Package Manager)** - Download frameworks, runtimes, apps

#### 2.4.2 WinGet Integration
- Microsoft Windows Package Manager (https://github.com/microsoft/winget-cli)
- Download .NET Runtimes (6, 7, 8)
- Download VC++ Runtimes (2015-2022)
- Download other Microsoft components
- Offline package download capability
- Fallback when DISM sources unavailable

#### 2.4.3 MSDT Integration
- Deployment Image Servicing and Management (DISM)
- System File Checker (SFC)
- CHKDSK integration
- BitLocker repair
- Windows Recovery Environment (WinRE)

#### 2.4.4 Tweaks Module (Optional)
- **Separate module** from core repair functionality
- Applied during or after repair based on user preference
- Categories:
  - **Privacy** - Disable telemetry, tracking
  - **Performance** - Disable visual effects, services
  - **Start Menu** - Pin/unpin, layout customization
  - **UI** - Theme, colors, taskbar settings
  - **Bloatware** - Remove pre-installed apps
- User chooses: repair-only OR repair + tweaks

### 2.5 Speed Optimization

#### 2.5.1 RAM-First Architecture
- Full OS runs in tmpfs
- All analysis tools in RAM
- Database caching in RAM
- Parallel processing enabled

#### 2.5.2 Caching Strategy
- Local hash database (pre-built)
- Smart download caching
- Session persistence to USB

---

## 3. Technical Specifications

### 3.1 System Requirements

#### Hardware
- **Minimum:** 4GB RAM (8GB recommended)
- **Storage:** 32GB USB (64GB recommended for offline packages)
- **CPU:** x86_64 compatible

#### Software Stack
- **Base OS:** Debian/Ubuntu-based live system
- **Kernel:** Latest LTS with NTFS-3G support
- **AI Runtime:** Python 3.10+ with PyTorch (CPU optimized)
- **Database:** SQLite for local hash stores

### 3.2 Directory Structure

```
/rescue-stick/
├── ai_core/
│   ├── diagnostic_engine.py       # Main AI orchestration
│   ├── adaptive_confidence.py    # Synoptic Executive-inspired threshold
│   ├── pattern_taxonomy.py       # Cross-domain pattern matching
│   ├── hash_database.py
│   ├── repair_strategies.py
│   └── models/
├── engines/                       # Holographic-style parallel engines
│   ├── 00_safety_evaluation.py   # Pre-repair safety checks, veto power
│   ├── 01_oracle.py              # Multiple diagnostic perspectives
│   ├── 02_file_scanner.py        # System breakdown - file analysis
│   ├── 03_registry_parser.py     # Registry hive analysis
│   ├── 04_event_log_engine.py    # Event log error parsing
│   ├── 05_hash_verifier.py       # Integrity checking
│   ├── 06_diagnostic_synthesis.py # Integrate all findings
│   ├── 07_memory.py              # Session continuity
│   ├── 08_learning.py            # Outcome tracking, improve over time
│   └── 09_risk_assessment.py     # Emotional/risk factors for repairs
├── windows_analyzer/
│   ├── file_scanner.py
│   ├── registry_parser.py
│   ├── event_log_reader.py
│   └── hash_verifier.py
├── repair_modules/
│   ├── file_replacer.py
│   ├── registry_restorer.py
│   ├── boot_repair.py
│   └── update_repair.py
├── network/
│   ├── msdt_integration.py
│   ├── windows_update_api.py
│   ├── download_manager.py
│   └── winget_integration.py     # WinGet for offline package downloads
├── ui/
│   ├── terminal_interface.py
│   └── web_dashboard.py (optional)
├── data/
│   ├── hash_database.db
│   ├── windows_baseline/
│   ├── dll_cache/                 # Cached DLLs for offline repair
│   └── package_cache/            # WinGet packages
└── tools/
    ├── chntpw
    ├── ntfs-3g
    ├── dism
    ├── winget-cli                 # Windows Package Manager
    └── windows-repair-tools/
```

---

## 4. User Interface

### 4.1 Primary Interface: Terminal/TUI
- Step-by-step diagnostic flow
- Progress indicators
- Risk warnings with confirmations
- Repair preview before execution

### 4.2 Optional: Web Dashboard
- Modern browser-based UI
- Real-time status visualization
- Detailed diagnostic reports
- Remote assistance capability

---

## 5. Linux Support (Phase 2)

### 5.1 Planned Features
- Package manager integration (apt, dnf, pacman)
- Bootloader repair (GRUB)
- Systemd service recovery
- Kernel module analysis
- File system integrity check

---

## 6. Security Considerations

- Read-only by default (mount target OS read-only for analysis)
- Backup before any repair operation
- Audit logging of all changes
- Rollback capability
- Network isolation option (air-gapped mode)

---

## 7. Development Phases

### Phase 1: Windows Core (MVP)
- File scanner and hash verification
- Registry parser
- Basic repair actions
- DISM/SFC integration

### Phase 2: AI Integration
- Diagnostic engine
- Strategy generation
- Cloud database sync

### Phase 3: Polish & Optimization
- UI improvements
- Caching optimization
- Hardware compatibility

### Phase 4: Linux Support
- Linux diagnostics
- Boot repair
- Package manager integration

---

## 8. Non-Functional Requirements

- **Performance:** Full diagnostic scan < 15 minutes on SSD
- **Reliability:** Pre-repair backup mandatory
- **Usability:** No technical knowledge required for basic mode
- **Compatibility:** Windows 10/11, Windows Server 2019+
- **Offline:** Core functionality without network

---

*Document Version: 1.0*  
*Created: 2026-03-25*