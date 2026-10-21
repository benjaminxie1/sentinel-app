# Sentinel Research & Engineering Notes

## 1. Computer Vision in Supplementary Fire Safety
Early flame and smoke detection using optical sensors (RGB cameras) offers significant spatial awareness advantages over ionization or photoelectric point detectors:
1. **Volumetric Coverage**: A single wide-angle security camera can monitor large open spaces (warehouses, loading docks, atriums) where ceiling-mounted smoke detectors experience delayed response due to thermal stratification.
2. **Pre-Flame Smoke Plume Tracking**: Smoke signatures typically precede open combustion. Visual smoke detection enables an earlier intervention window before thermal alarms trigger.
3. **Verification Speed**: High-resolution video frames provide security teams and dispatchers with instant situational assessment before on-site dispatch.

---

## 2. Threshold Calibration & Environmental Compensation

### Multi-Tier Confidence Thresholds
To balance early warning with operational fatigue from false alarms, Sentinel implements a 3-tier classification strategy:
* **P1 - Immediate Critical Alert (`confidence >= 0.95`)**: Unambiguous visual flame/smoke signature. Automatically pushes urgent SMS, email, and audible local siren/desktop alert.
* **P2 - Human Verification Queue (`0.85 <= confidence < 0.95`)**: Moderate confidence detection flagged in the monitoring console for operator confirmation within 60 seconds.
* **P4 - Informational Telemetry (`0.70 <= confidence < 0.85`)**: Ambient logging and telemetry collection for retrospective model fine-tuning.

### Environmental Compensation Filters
- **Twilight & Direct Sunlight Compensation**: Low-angle direct sunlight during sunset hours (typically 17:00–19:00 depending on latitude and season) produces specular reflections off metallic or reflective surfaces that can resemble flickering flames. Sentinel applies a dynamic threshold offset (+0.05 to +0.08) during configurable sunset windows.
- **Fog and Particulate Compensation**: Ambient particulate scattering (fog, steam, heavy dust) alters optical contrast. Atmospheric contrast filters reduce sensitivity during dense fog to prevent false alarms while maintaining flame detection sensitivity.

---

## 3. Optical & Sensor Fusion

While optical cameras provide wide-area spatial coverage, physical environmental sensors provide orthogonal verification:
- **Optical (YOLOv8)**: Fast spatial localization, flame/smoke area bounding, and visual plume spread velocity.
- **Microcontroller Integration (Arduino Mega / ESP32)**:
  - **MQ-2 / MQ-135 Gas Sensors**: Volatile organic compounds and combustion gases (CO, LPG, smoke).
  - **IR Flame Detectors**: 760nm–1100nm infrared radiation sensitivity.
  - **DHT22 / BME280**: Ambient temperature rapid rate-of-rise ($> 5^\circ\text{C} / \text{min}$).
- When optical detection correlates with a physical rate-of-rise or sensor trigger, confidence score is elevated to P1 dispatch status.

---

## 4. Edge Reliability & Continuous Operation Findings

Field deployments revealed several critical edge engineering constraints:
1. **GPU Thermal Throttling**: Continuous multi-stream inference on edge GPUs can induce thermal throttling without frame rate regulation. Sentinel runs camera sampling at an optimized 2 FPS inference cycle per camera feed rather than full camera native frame rate (30 FPS), reducing GPU thermal load by ~75% while maintaining sub-2-second alert latency.
2. **Offline-First Architecture**: Network partitions must never disable local fire monitoring. Alert logic, model inference, and local database storage operate completely autonomously on the local edge appliance. Outbound SMS/email queues are buffered locally and re-transmitted once external network links are restored.
3. **Automated Dual-Network Failover**: The system actively monitors WAN connectivity via primary Ethernet. Upon interface loss, it automatically activates cellular failover within 30 seconds to deliver critical notifications.
