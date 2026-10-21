# Maintainers & Project Governance

This document outlines the maintainer team, triage policies, review responsibilities, and release processes for the **Sentinel Fire Detection System**.

---

## 👥 Maintainer Team

| Name | Role | GitHub | Responsibilities |
| :--- | :--- | :--- | :--- |
| **Benjamin Xie** | **Project Lead & Primary Maintainer** | [@benjaminxie1](https://github.com/benjaminxie1) | System architecture, computer vision models, core engine, release management, and issue triage |
| **Kevin Fei** | **Core Maintainer** | [@Fairhain](https://github.com/Fairhain) | Hardware integration, Arduino sensor bridge, and edge deployment scripts |
| **Mihir Bamdhamvamvuri** | **Core Maintainer** | [@Phenixrigh](https://github.com/Phenixrigh) | Model training pipelines, dataset management, and field testing |

---

## 📋 Maintainer Responsibilities

### 1. Issue Triage & Response SLA
- **Initial Triage**: Maintainers review new issues within **48–72 hours**.
- **Labeling**: Apply appropriate labels (`bug`, `enhancement`, `triage`, `documentation`, `security`).
- **Reproduction**: For reported edge failures, verify camera stream protocols (RTSP/ONVIF), environment parameters, and hardware configuration.

### 2. Pull Request Review Process
- All non-trivial PRs require review and approval from at least one core maintainer before merging.
- **Review Criteria**:
  1. **Supplementary Safety Integrity**: Code contributions must strictly uphold Sentinel’s status as a *supplementary* early-warning system and must not degrade fail-safe defaults.
  2. **Offline-First Resilience**: Critical detection loops, local SQLite logging, and desktop sirens must have zero cloud dependencies.
  3. **Inference Latency Target**: Frame processing must not breach the $< 2.0$-second latency ceiling.
  4. **Test Coverage**: Bug fixes and features must include unit or integration test cases in `tests/`.

### 3. Release Management
- Sentinel follows [Semantic Versioning 2.0.0](https://semver.org/).
- **Release Cadence**:
  - **Patch Releases (`x.y.Z`)**: As needed for bug fixes, driver compatibility updates, or security patches.
  - **Minor Releases (`x.Y.0`)**: Monthly or quarterly for new features, hardware sensor integrations, and UI enhancements.
  - **Major Releases (`X.0.0`)**: For breaking configuration changes or architecture rewrites.
- Every release includes signed git tags, automated CI builds, and full changelog updates in `CHANGELOG.md`.

---

## 🔒 Security Vulnerability Reporting

Security is paramount in safety-adjacent systems. If you discover a vulnerability or security flaw, please do not file a public issue. Instead, report it privately to the primary maintainer at:
- **Email**: `bxie2015@gmail.com`
- Maintainers will acknowledge within 24 hours and coordinate a patch within 7 days.
