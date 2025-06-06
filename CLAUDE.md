# Fire Detection System - Development Guide

## CRITICAL LEGAL DISCLAIMER
**This system is a SUPPLEMENTARY early warning tool only.**
- Does NOT replace UL-listed fire detection systems
- Must NEVER be used as primary fire detection
- NOT for use in sleeping areas without certified systems
- Always maintain certified fire alarm systems

## Project Overview
Open-source supplementary fire detection using existing RGB cameras to provide early warning alerts. Enhances, not replaces, traditional fire safety systems through automated 24/7 monitoring.

## Core Architecture - Simplified for Reliability

### Single Algorithm Approach
- **YOLOv8 Visual Pattern Recognition** on RGB camera feeds
- **Completely offline operation** - no internet dependency for detection
- **Configurable threshold system** via YAML config files
- **Real-time processing** optimized for standard security cameras

### Key Design Principles
- **Safety over features** - conservative detection thresholds
- **Offline-first** - complete functionality without internet
- **Configurable** - threshold tuning without code changes
- **Reliable** - simple architecture, minimal failure points
- **Supplementary positioning** - always emphasizes additional safety layer

## Technical Stack (Production-Ready)
- **Application**: Tauri (single binary, cross-platform)
- **Detection Engine**: Python 3.10+ with PyTorch + YOLOv8
- **Computer Vision**: OpenCV for camera integration
- **Database**: Embedded SQLite for local storage
- **Configuration**: YAML-based threshold management
- **Platform**: Windows 10/11 Pro or Linux

## Hardware Requirements
- Business-grade desktop PC (16GB RAM, 500GB SSD)
- NVIDIA RTX 3060+ GPU (required for real-time processing)
- 1-2 hour UPS backup power
- Dual network connectivity (ethernet + cellular)
- Existing RGB security cameras (RTSP/ONVIF)

## Detection Logic
```yaml
# Configurable thresholds
immediate_alert: 0.95    # P1 - dispatch immediately  
review_queue: 0.85       # P2 - human verification
log_only: 0.70          # P4 - data collection

# Environmental adjustments
fog_adjustment: -0.05    # Reduce sensitivity in poor visibility
sunset_hours: [17, 19]   # Higher thresholds during challenging light
```

## Development Priorities

### Core Detection System
1. **Camera Integration** - RTSP stream processing with OpenCV
2. **YOLOv8 Implementation** - Fire/smoke pattern recognition
3. **Configuration System** - YAML-based threshold management
4. **Alert Generation** - Local notifications and logging
5. **Basic GUI** - Tauri-based monitoring interface

### Success Criteria
- Process 5-10 camera feeds simultaneously
- <2 second detection latency
- Configurable confidence thresholds
- Local alert generation (SMS, email when network available)
- 24/7 operation with graceful failure handling

## Compliance & Safety

### Standards Adherence
- NFPA 1221 (Emergency Communications) guidelines
- Local fire safety regulations compliance
- Privacy law compliance (data retention limits)
- Equipment certification where required

### Documentation Requirements
- Installation and configuration procedures
- Operator training materials
- Incident reporting templates
- Performance metrics and audit trails

## Development Commands

### Testing
- Run detection tests: `python -m pytest tests/`
- Performance benchmarks: `python scripts/benchmark.py`
- Configuration validation: `python scripts/validate_config.py`

### Deployment
- Build Tauri application: `cargo tauri build`
- Package for distribution: `cargo tauri bundle`
- System health check: `python scripts/health_check.py`

## Current Focus
Implementing core detection engine and basic monitoring interface. Focus on reliability, configurability, and real-world performance validation.

---

**Remember**: This is a supplementary safety system. Every implementation must emphasize its role as an additional layer of protection, never a replacement for certified fire detection systems.