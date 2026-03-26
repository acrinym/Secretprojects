# RescueStick AI

AI-powered Windows rescue system on a USB stick. Runs in RAM, diagnoses issues, repairs without reinstalling.

## What It Does

- **Boot from USB** → Runs Linux in RAM (super fast)
- **Scans Windows** → Files, registry, event logs
- **AI diagnoses** → Uses holographic multi-engine architecture
- **Repairs intelligently** → Fixes specific files/registry, not the whole OS

## Architecture - 10 Holographic Engines

| # | Engine | Status |
|---|--------|--------|
| 00 | Safety Evaluation | ✅ SPEC DONE |
| 01 | Oracle | ✅ SPEC DONE |
| 02 | File Scanner | ✅ SPEC DONE |
| 03 | Registry Decorrupter | ✅ SPEC DONE |
| 04 | Event Log Engine | ✅ SPEC DONE |
| 05 | Hash Verifier | ✅ SPEC DONE |
| 06 | Diagnostic Synthesis | ✅ SPEC DONE |
| 07 | Memory | ✅ SPEC DONE |
| 08 | Learning | ✅ SPEC DONE |
| 09 | Risk Assessment | ✅ SPEC DONE |

## Documentation

- [SPEC.md](SPEC.md) - Main specification
- [ENGINES.md](ENGINES.md) - Build order and dependencies
- [docs/](docs/) - Individual engine specifications (10 complete)
- [docs/SOURCES.md](docs/SOURCES.md) - Offline data sources (registry baselines, GitHub tools, WinGet)

## Why Better Than MSDT/SFC/DISM Alone

- **AI reads everything** → knows exactly what's broken
- **Granular repair** → no wiping, surgical fixes
- **Runs in RAM** → no speed issues
- **Adaptive confidence** → learns from outcomes
- **Multi-perspective diagnosis** → Oracle engine sees what others miss

---

*Project started: 2026-03-25*