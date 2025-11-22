import random
import time

import numpy as np
import requests

API_URL = "http://localhost:8000/predict"


def generate_normal_data():
    """Generates data similar to Iris dataset mean/std"""
    return {
        "sepal length (cm)": abs(np.random.normal(5.8, 0.8)),
        "sepal width (cm)": abs(np.random.normal(3.0, 0.4)),
        "petal length (cm)": abs(np.random.normal(3.7, 1.7)),
        "petal width (cm)": abs(np.random.normal(1.2, 0.7)),
    }


def generate_drifted_data():
    """
    Generates data with significantly higher values to cause drift.
    Simulates a sensor malfunction or environment change.
    """
    return {
        "sepal length (cm)": abs(np.random.normal(5.8, 0.8)) + 2.5,  # Drift!
        "sepal width (cm)": abs(np.random.normal(3.0, 0.4)) - 1.0,  # Drift!
        "petal length (cm)": abs(np.random.normal(3.7, 1.7)) + 3.0,  # Drift!
        "petal width (cm)": abs(np.random.normal(1.2, 0.7)),
    }


def run_simulation(mode="normal", steps=50):
    print(f"--- Starting Simulation: {mode.upper()} Traffic ---")
    for i in range(steps):
        if mode == "drift":
            data = generate_drifted_data()
        else:
            data = generate_normal_data()

        try:
            resp = requests.post(API_URL, json=data)
            print(f"[{i+1}/{steps}] {mode} request sent. Status: {resp.status_code}")
        except Exception as e:
            print(f"Error: {e}")

        # Random sleep to simulate real traffic patterns for Grafana
        time.sleep(random.uniform(0.1, 0.5))


if __name__ == "__main__":
    print("=" * 80)
    print("ML Model Simulator - Automatic Drift Detection Enabled")
    print("=" * 80)

    print("\n1. Sending Normal Traffic...")
    run_simulation("normal", 50)

    print("\n2. Sending Drifted Traffic (Simulating Issue)...")
    run_simulation("drift", 50)

    print("\n" + "=" * 80)
    print("Simulation Complete!")
    print("=" * 80)
    print("\n📊 AUTOMATIC DRIFT DETECTION:")
    print("   - Drift reports are automatically generated every 5 minutes")
    print("   - View latest report: http://localhost:8080/drift_report_latest.html")
    print("   - Check monitoring status: http://localhost:8000/monitor/status")
    print("\n⚡ MANUAL OPTIONS (if you need immediate results):")
    print("   - Trigger report now: http://localhost:8000/monitor/trigger_now (POST)")
    print("   - Generate manual report: http://localhost:8000/monitor/generate_report")
    print(
        "\nWait a few minutes or trigger manually to see the drift detection results!"
    )
    print("=" * 80)
