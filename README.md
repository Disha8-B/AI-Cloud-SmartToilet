# Development of Smart Toilet — PRJ_283

Runnable software prototype based on the Review-1 presentation. Requirements: Python 3.9+; no external packages, sensors, or cloud account.

## Run

In this folder, run `python app.py`, then open http://localhost:8000. The application generates 40 simulated readings on first launch. Add a reading with the form to see an alert. To reset, stop the app and delete `smart_toilet.db`.

## API and logic

`GET /api/readings`: latest 100 readings. `GET /api/summary`: counts and average. `POST /api/readings`: JSON containing facility (string), occupancy (0–100 integer), air_quality (0–100 integer, higher worse), water_level (0–100 integer), water_liters (0–720), hours_since_clean (0–720). Data is persisted in a local SQLite database.

Risk = min(35, floor(2 × hours_since_clean)) + min(25, floor(0.25 × occupancy)) + 25 when air_quality >= 70 + 15 when water_level <= 20; capped at 100. Cleaning alert if risk >= 65. Anomaly if air_quality >= 80, water_level <= 10, or water_liters exceeds both 15 L and 2.5 times the mean of at least five previous readings for the same facility.

## Scope

This is a locally running cloud-style simulation. It does not connect to ESP32 sensors, deploy Firebase, send external notifications, train an ML model, or validate performance on real-world data. Future work would connect a secured telemetry endpoint and labelled field data to train and compare a predictive model.
