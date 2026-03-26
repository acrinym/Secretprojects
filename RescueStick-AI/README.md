# RescueStick AI

AI-powered Windows rescue system on a USB stick. Runs in RAM, diagnoses issues, repairs without reinstalling.

## What It Does

- **Boot from USB** → Runs Linux in RAM (super fast)
- **Scans Windows** → Files, registry, event logs
- **AI diagnoses** → Uses holographic multi-engine architecture
- **Repairs intelligently** → Fixes specific files/registry, not the whole OS

## Architecture

Uses 10 parallel engines (inspired by HolographicEngines):

- 00_safety - Pre-repair safety checks
- 01_oracle - Multiple diagnostic perspectives  
- 02_file_scanner - System file hash verification
- 03_registry_parser - Registry hive analysis & repair
- 04_event_log_engine - Windows event log parsing
- 05_hash_verifier - Integrity checking
- 06_diagnostic_synthesis - Integrate all findings
- 07_memory - Session continuity
- 08_learning - Outcome tracking
- 09_risk_assessment - Repair risk evaluation

## Documentation

- [SPEC.md](SPEC.md) - Main specification
- [ENGINES.md](ENGINES.md) - Build order and dependencies
- [docs/](docs/) - Individual engine specifications

## Current Status

**3/10 engines specified:**
- 02 File Scanner - DONE
- 03 Registry Decorrupter - DONE  
- 04 Event Log Engine - DONE

## Why Better Than MSDT/SFC/DISM Alone

- **AI reads everything** → knows exactly what's broken
- **Granular repair** → no wiping, surgical fixes
- **Runs in RAM** → no speed issues
- **Adaptive confidence** → learns from outcomes

---

*Project started: 2026-03-25*