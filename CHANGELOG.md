# Changelog

All notable changes to the Sentinel Fire Detection System are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.1] - 2026-10-21

### Added
- Standardized open-source repository configuration with Apache-2.0 License.
- Formal `CONTRIBUTING.md` guidelines detailing safety rules, code formatting (`black`, `flake8`), and pull request workflows.
- GitHub Actions CI workflow (`.github/workflows/ci.yml`) testing on Python 3.10, 3.11, and 3.12, with frontend build validation on Node 20.
- Standardized GitHub Issue Forms (`bug_report.yml`, `feature_request.yml`) and Pull Request template.
- Unit testing suite in `tests/test_detection.py` covering `Detection` and `DetectionResult` prioritization.
- In-depth hardware and edge computing specification documents (`docs/requirements.md` and `docs/research_notes.md`).

### Changed
- Refactored `package.json` to resolve syntax validation errors and added comprehensive metadata.
- Polished `config/detection_config.yaml` and `requirements.txt` formatting.
- Updated `README.md` with non-red golden warning callouts (`[!WARNING]`), architecture diagrams, and 2-year project evolution milestones.

---

## [0.2.0] - 2026-09-15

### Added
- Upgraded desktop shell to Tauri v2 stable with secure IPC command handlers.
- Hardened local REST API CORS and WebSocket origin verification policies.
- Multi-interface network monitoring daemon with automated cellular/ethernet failover triggers within 30 seconds.
- GPU tensor memory pooling to reduce VRAM fragmentation during 10+ concurrent RTSP camera processing.

### Fixed
- Addressed memory pressure on long-running RTSP ingestion queues via circular memory buffering.
- Fixed non-standard ONVIF discovery probe timeouts on commercial cameras using custom HTTP ports.

---

## [0.1.5] - 2026-03-22

### Added
- Hardware sensor fusion bridge (`backend/hardware/arduino_bridge.py`) supporting MQ-2/MQ-135 gas and IR flame sensors at 115200 baud.
- Microcontroller binary packet parser with CRC validation.
- Camera health scoring system and automated degradation alerts for lens occlusions.
- Benchmark profiling suite (`scripts/benchmark.py`) for inference latency verification.

### Changed
- Optimized RTSP stream reconnection backoff strategy with randomized jitter to prevent camera connection throttling.
- Dynamic twilight glare compensation offset applied between 17:00 and 19:00 hours.

---

## [0.1.0] - 2025-09-20

### Added
- Initial public open-source repository structure migrated from internal GitLab development.
- Core YOLOv8 fire and smoke detection engine with multi-camera RTSP ingestion.
- Multi-tier alert classification (P1 Immediate, P2 Verification Queue, P4 Logging).
- Local SQLite database logging and circular video clip buffering.
- Tauri desktop surveillance interface with live multi-camera grid.
