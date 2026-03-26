# RescueStick AI - Engine Build Order & Dependencies

This document lists all engines needed, their purposes, and what's required to build each one.

---

## Engine List (Holographic Architecture)

| # | Engine | Purpose | Status | Priority |
|---|--------|---------|--------|----------|
| 00 | Safety Evaluation | Pre-repair safety checks, veto dangerous operations | - | P0 |
| 01 | Oracle | Multiple diagnostic perspectives | - | P1 |
| 02 | File Scanner | System file hash verification | [SPEC DONE](docs/02_File_Scanner.md) | P0 |
| 03 | Registry Parser | Registry hive analysis & repair | [SPEC DONE](docs/03_Registry_Decorrupter.md) | P0 |
| 04 | Event Log Engine | Windows event log parsing | [SPEC DONE](docs/04_Event_Log_Engine.md) | P1 |
| 05 | Hash Verifier | Integrity checking against baselines | TODO | P1 |
| 06 | Diagnostic Synthesis | Integrate all findings | TODO | P1 |
| 07 | Memory | Session continuity | TODO | P2 |
| 08 | Learning | Outcome tracking, improve over time | TODO | P2 |
| 09 | Risk Assessment | Repair risk evaluation | TODO | P2 |

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
```

**Data needed:**
- Registry baselines for each Windows version
- DLL cache (msvcp140.dll, vcruntime140.dll, etc.)
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
**TODO - Need spec**

What it does:
- Compare scanned hashes to baseline
- Score file integrity
- Prioritize repairs

Dependencies:
- SQLite for hash database

Data needed:
- All baseline databases from Engine 02

---

### ENGINE 06: Diagnostic Synthesis
**TODO - Need spec**

What it does:
- Combine all engine findings
- Generate repair strategy
- Calculate confidence scores

Dependencies:
- All other engines

---

### ENGINE 00: Safety Evaluation
**TODO - Need spec**

What it does:
- Check if repair is safe
- Veto dangerous operations
- Require user confirmation for risky repairs

Dependencies:
- Rule database

---

### ENGINE 01: Oracle
**TODO - Need spec**

What it does:
- Multiple diagnostic perspectives
- "What would a sysadmin think?"
- "What would malware look for?"

---

### ENGINE 07: Memory
**TODO - Need spec**

What it does:
- Session continuity
- Remember previous scans
- Track changes between sessions

---

### ENGINE 08: Learning
**TODO - Need spec**

What it does:
- Track repair outcomes
- Improve confidence over time
- Learn from successes/failures

---

### ENGINE 09: Risk Assessment
**TODO - Need spec**

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
4. Engine 05 (Hash Verifier) - tied to 02
5. Engine 06 (Synthesis) - makes decisions
6. Engine 00 (Safety) - prevents bricked systems

**Phase 2 (Intelligence):**
6. Engine 04 (Event Logs)
7. Engine 01 (Oracle)

**Phase 3 (Polish):**
8. Engine 07 (Memory)
9. Engine 08 (Learning)
10. Engine 09 (Risk Assessment)

---

## How to Contribute

1. Pick an engine marked "TODO"
2. Create `/docs/{XX}_{Engine_Name}.md`
3. Document what it does, how to build it
4. List dependencies and data needed
5. Commit to repo

---

*Last Updated: 2026-03-25*
*Build Status: 2/10 engines specified*