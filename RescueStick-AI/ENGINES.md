# RescueStick AI - Engine Build Order & Dependencies

This document lists all 20 engines needed, their purposes, and what's required to build each one.

---

## Engine List (Holographic Architecture)

| # | Engine | Purpose | Status | Priority |
|---|--------|---------|--------|----------|
| 00 | Safety Evaluation | Pre-repair safety checks, veto dangerous operations | [SPEC DONE](docs/00_Safety_Evaluation.md) | P0 |
| 01 | Oracle | Multiple diagnostic perspectives | [SPEC DONE](docs/01_Oracle.md) | P1 |
| 02 | File Scanner | System file hash verification | [SPEC DONE](docs/02_File_Scanner.md) | P0 |
| 03 | Registry Decorrupter | Registry hive analysis & repair | [SPEC DONE](docs/03_Registry_Decorrupter.md) | P0 |
| 04 | Event Log Engine | Windows event log parsing | [SPEC DONE](docs/04_Event_Log_Engine.md) | P1 |
| 05 | Hash Verifier | Integrity checking against baselines | [SPEC DONE](docs/05_Hash_Verifier.md) | P1 |
| 06 | Diagnostic Synthesis | Integrate all findings | [SPEC DONE](docs/06_Diagnostic_Synthesis.md) | P1 |
| 07 | Memory | Session continuity | [SPEC DONE](docs/07_Memory.md) | P2 |
| 08 | Learning | Outcome tracking, improve over time | [SPEC DONE](docs/08_Learning.md) | P2 |
| 09 | Risk Assessment | Repair risk evaluation | [SPEC DONE](docs/09_Risk_Assessment.md) | P2 |
| 10 | Snapshot | Time machine / instant rollback | IN SPEC | P1 |
| 11 | Crowd Intel | Anonymous pattern sharing | IN SPEC | P3 |
| 12 | Hardware Check | Memory/disk/CPU diagnostics | IN SPEC | P2 |
| 13 | Malware Guard | ClamAV malware integration | IN SPEC | P1 |
| 14 | Recovery Console | Windows RE-like environment | IN SPEC | P1 |
| 15 | Driver Cache | Offline driver database | IN SPEC | P2 |
| 16 | AI Assistant | Natural language repair | IN SPEC | P2 |
| 17 | Live Patch | Hot-patch without reboot | IN SPEC | P3 |
| 18 | Multi-Dashboard | Manage multiple PCs | IN SPEC | P3 |
| 19 | Auto Flows | Pre-built repair sequences | IN SPEC | P1 |
| 20 | Media Gen | Custom rescue media builder | IN SPEC | P3 |

---

## Engine Dependencies & Data Requirements

### ENGINE 02: File Scanner
**Done:** `/docs/02_File_Scanner.md`

**Dependencies to install:**
```bash
# Linux packages
sudo apt-get install ntfs-3g sleuthkit libtsk-dev

# Python packages  
pip install pytsk pytsk3 yara-python
```

**Data needed:**
- Hash baselines for each Windows version (Win10 20H2, 21H2, 22H2, Win11 22H2, 23H2, Server 2019, 2022)
- Build by scanning clean Windows installs → store in SQLite

**How to get baselines:**
1. Download Windows evaluation VMs from Microsoft
2. Boot, run scanner on clean install
3. Export to SQLite database

---

### ENGINE 03: Registry Decorrupter
**Done:** `/docs/03_Registry_Decorrupter.md`

**Dependencies to install:**
```bash
# Linux packages
sudo apt-get install libhivex-bin chntpw reglookup wine

# Python packages
pip install hivex construct pefile

# WinGet (Windows Package Manager) for downloading packages
# Download from: https://github.com/microsoft/winget-cli/releases
# Put in: /rescue-stick/tools/winget/
```

**Data needed:**
- Registry baselines for each Windows version
- DLL cache (msvcp140.dll, vcruntime140.dll, etc.)
- WinGet package cache (.NET, VC++ runtimes)
- Known-good registry values database

**How to get baselines:**
1. From clean Windows installs, copy:
   - Windows/System32/config/SYSTEM
   - Windows/System32/config/SOFTWARE
   - Windows/System32/config/SECURITY
   - Windows/System32/config/SAM

**DLL Sources:**
- dll-files.com (check terms)
- Microsoft Update Catalog
- DISM /Get-FileInfo

---

### ENGINE 04: Event Log Engine
**Done:** `/docs/04_Event_Log_Engine.md`

What it does:
- Parse Windows .evtx event log files
- Extract error patterns, crash dumps
- Correlate with file/registry issues

Dependencies:
```bash
sudo apt-get install libevtx-dev
pip install python-evtx evtx
```

Data needed:
- Event ID database (JSON mapping event IDs to meanings)
- Known error code mappings

---

### ENGINE 05: Hash Verifier
**Done:** `/docs/05_Hash_Verifier.md`

What it does:
- Compare scanned hashes to baseline databases
- Score file integrity (0-100%)
- Prioritize repairs by severity

Dependencies:
- SQLite3 (built-in)
- pefile (for version detection)

Data needed:
- Baseline databases (from Engine 02)

---

### ENGINE 06: Diagnostic Synthesis
**Done:** `/docs/06_Diagnostic_Synthesis.md`

What it does:
- Integrate findings from all engines
- Correlate related issues
- Generate repair strategy

Dependencies:
- All other engines' outputs

---

### ENGINE 00: Safety Evaluation
**Done:** `/docs/00_Safety_Evaluation.md`

What it does:
- Pre-repair safety checks
- Veto dangerous operations
- Require user confirmation
- Create backups before changes

Dependencies:
- Pre-repair backup system

---

### ENGINE 01: Oracle
**Done:** `/docs/01_Oracle.md`

What it does:
- Multiple diagnostic perspectives (6 angles)
- "What would a sysadmin think?"
- "What would malware look for?"
- Forensic, performance, security views

---

### ENGINE 07: Memory
**Done:** `/docs/07_Memory.md`

What it does:
- Session continuity
- Remember previous scans
- Track changes between sessions

---

### ENGINE 08: Learning
**Done:** `/docs/08_Learning.md`

What it does:
- Track repair outcomes
- Improve confidence over time
- Learn from successes/failures

---

### ENGINE 09: Risk Assessment
**Done:** `/docs/09_Risk_Assessment.md`

What it does:
- Evaluate repair risk
- Consider emotional factors (user panic level)
- Recommend escalation path

---

## Quick Start - Build Priority Order

**Phase 1 (MVP):**
1. Engine 02 (File Scanner) - [SPEC DONE](docs/02_File_Scanner.md) - core functionality
2. Engine 03 (Registry) - [SPEC DONE](docs/03_Registry_Decorrupter.md) - core functionality
3. Engine 04 (Event Log) - [SPEC DONE](docs/04_Event_Log_Engine.md)
4. Engine 05 (Hash Verifier) - [SPEC DONE](docs/05_Hash_Verifier.md) - tied to 02
5. Engine 06 (Synthesis) - [SPEC DONE](docs/06_Diagnostic_Synthesis.md) - makes decisions
6. Engine 00 (Safety) - [SPEC DONE](docs/00_Safety_Evaluation.md) - prevents bricked systems

**Phase 2 (Intelligence):**
7. Engine 01 (Oracle) - [SPEC DONE](docs/01_Oracle.md) - multiple perspectives

**Phase 3 (Polish):**
8. Engine 07 (Memory) - [SPEC DONE](docs/07_Memory.md) - session continuity
9. Engine 08 (Learning) - [SPEC DONE](docs/08_Learning.md) - outcome tracking
10. Engine 09 (Risk Assessment) - [SPEC DONE](docs/09_Risk_Assessment.md) - repair risk

---

## Documentation Files

| File | Purpose |
|------|---------|
| [SPEC.md](../SPEC.md) | Main specification |
| [ENGINES.md](./ENGINES.md) | Build order and dependencies |
| [docs/](./docs/) | Individual engine specs (10 complete) |
| [docs/BUILD.md](./docs/BUILD.md) | How to build RescueStick |
| [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md) | Deployment options (USB, Medicat, ISO) |
| [docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md) | Common issues and fixes |
| [docs/SOURCES.md](./docs/SOURCES.md) | Offline data sources |

---

## All Engine Specs Complete ✅

All 10 engines have full specifications with:
- What it does
- How to build (step-by-step code)
- Dependencies (apt/pip)
- Data needed
- Testing instructions

---

*Last Updated: 2026-03-26*
*Build Status: 10/20 engines specified (10 in docs/, 11 in SPEC.md)*