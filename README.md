# Cloud Collectors: Automated Deployable Rainwater Harvesting System

This repository contains the core software architecture and control logic for the "Cloud Collectors" project, an IoT-driven deployable rainwater harvesting (RWH) system designed for constrained urban environments.

## System Architecture

The automation logic is built on a two-tier edge-to-gateway architecture:
1. **Edge Node (ESP32):** Handles local telemetry (ultrasonic water level, pH, turbidity) and controls the mechanical actuators via MQTT.
2. **Gateway (Raspberry Pi / Python):** Runs the `RainwaterController` hybrid decision engine.

## Core Features
* **Hybrid Decision Matrix:** Correlates real-time NASA POWER / OpenWeatherMap API data with local edge-sensor inputs to predict optimal harvesting windows.
* **Wind-Safe Autonomous Protocol:** An emergency override script that forces a "Safe-Stow" state within 1.1 seconds if wind velocities exceed 12.5 m/s, preventing aeroelastic failure of the primary structural arms.

## Repository Contents
* `main.py`: The primary Python control loop, API integration, and MQTT publisher.
* `requirements.txt`: Python dependency list.

## Authors
* **Ahmet Şamil Karadeniz** - Statistical Data & Efficiency Modeling
* **Alp Eren Karaca** - Control Logic, API Integration & "Wind-Safe" Protocols
* **Doğukan Veziroğlu** - Hardware Architecture & MQTT Synchronization
* **Gökay Yılmaz** - 3D Kinematics & CFD Simulations
