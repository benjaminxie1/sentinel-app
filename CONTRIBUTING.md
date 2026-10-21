# Contributing to Sentinel Fire Detection System

Thank you for your interest in contributing to **Sentinel**! Sentinel is an open-source supplementary fire and smoke detection platform combining computer vision, edge processing, and multi-sensor fusion.

Because Sentinel is designed for safety-critical environments, we uphold rigorous standards for code quality, architectural reliability, safety disclaimers, and automated testing.

---

## Code of Conduct

We are committed to providing a welcoming, inclusive, and harassment-free experience for everyone. Be respectful, constructive, and collaborative in discussions, issues, and code reviews.

---

## How to Contribute

### 1. Reporting Bugs
- **Check existing issues** first to avoid duplicates.
- Provide a clear and descriptive title.
- Include step-by-step reproduction instructions, logs (`/var/log/sentinel/sentinel.log` or local `logs/sentinel.log`), operating system details, and camera stream specifications (resolution, codec, RTSP URL format).

### 2. Suggesting Enhancements & New Features
- Open an Issue with the prefix `[Feature Request]: ...`.
- Describe the motivation, operational use-case, and why the feature benefits supplementary detection.
- Note any potential impacts on inference latency or edge memory footprint.

### 3. Submitting Pull Requests (PRs)
1. **Fork** the repository and create your feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Set up local development environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   npm install
   ```
3. **Format and lint**:
   ```bash
   black backend/ tests/
   flake8 backend/ tests/
   ```
4. **Run tests**:
   ```bash
   pytest tests/
   python scripts/validate_config.py
   ```
5. **Commit your changes**:
   Write meaningful commit messages following Conventional Commits (e.g., `feat: add camera latency health check`, `fix: handle rtsp stream disconnect reconnect backoff`).
6. **Open a Pull Request**:
   Describe the changes made, testing completed, and reference any associated issues.

---

## Development Principles & Safety Guidelines

1. **Supplementary Positioning**:
   - Sentinel is strictly a **supplementary early-warning system**.
   - Code contributions must **NEVER** imply or market Sentinel as a certified replacement for NFPA/UL/EN-certified primary fire detection systems.
2. **Offline-First Resilience**:
   - The primary vision loop and local SQLite alert logging must function without active internet connectivity. External notifications (SMS/Email) must fail gracefully with retry queues.
3. **Low Latency & Resource Efficiency**:
   - Video processing must adhere to the target detection latency ($< 2.0$ seconds). Avoid blocking calls on async event loops.
