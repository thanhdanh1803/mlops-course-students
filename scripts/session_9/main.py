import logging
import os
from datetime import datetime

import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from evidently import Report
from evidently.presets import DataDriftPreset
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- 1. Setup & Model Training (Simulation) ---
# TODO: In a real app, load a pickled model. Here, we train on startup for simplicity.
data = load_iris(as_frame=True)
df_reference = data.frame

# Simple model
model = RandomForestClassifier()
model.fit(df_reference.drop("target", axis=1), df_reference["target"])

# Mapping for readability
target_names = data.target_names

# Global store for production data (for demo purposes only - use a DB in production!)
# We keep a rolling window of the last 500 requests
production_data = []

app = FastAPI()

# --- 2. Instrumentation (Prometheus) ---
# This automatically creates the /metrics endpoint for Prometheus to scrape
instrumentator = Instrumentator().instrument(app).expose(app)


# --- 2.5. Automatic Drift Detection ---
# TODO: In a real app, we would use a database to store the production data.
# TODO: We would also use a more sophisticated drift detection algorithm.
# TODO: We would also use a more sophisticated drift detection algorithm.
def generate_drift_report_background():
    """
    Background task to automatically generate drift reports.
    Runs periodically without requiring manual API calls.
    """
    logger.info(
        f"[AUTOMATIC] Drift report generation triggered. Production data points: {len(production_data)}"
    )

    if len(production_data) < 10:
        logger.warning(
            "[AUTOMATIC] Not enough data to generate report. Skipping this cycle."
        )
        return

    try:
        # Create DataFrame from current logs
        df_current = pd.DataFrame(production_data)
        logger.debug(f"[AUTOMATIC] Current data shape: {df_current.shape}")

        # Feature list for drift detection
        features_list = [
            "sepal length (cm)",
            "sepal width (cm)",
            "petal length (cm)",
            "petal width (cm)",
        ]

        # Generate Report
        logger.info("[AUTOMATIC] Generating Evidently drift report...")
        report = Report([DataDriftPreset()])

        my_eval = report.run(
            reference_data=df_reference, current_data=df_current[features_list]
        )

        # Save report with timestamp
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(reports_dir, f"drift_report_{timestamp}.html")

        # Also save as latest for easy access
        latest_report_path = os.path.join(reports_dir, "drift_report_latest.html")

        logger.info(f"[AUTOMATIC] Saving report to {report_path}")
        my_eval.save_html(report_path)
        my_eval.save_html(latest_report_path)

        # Verify the file was created
        if os.path.exists(report_path):
            file_size = os.path.getsize(report_path)
            logger.info(
                f"[AUTOMATIC] Report successfully saved. Size: {file_size} bytes. Data points analyzed: {len(production_data)}"
            )
        else:
            logger.error(f"[AUTOMATIC] Report file was not created at {report_path}")

    except Exception as e:
        logger.error(f"[AUTOMATIC] Error generating drift report: {str(e)}")


# Initialize and start the background scheduler
# TODO: In a real app, we would use Airflow or Celery to schedule the background tasks.
scheduler = BackgroundScheduler()
# Run drift detection every 5 minutes (300 seconds)
# Adjust the interval based on your needs:
# - For testing: interval=60 (1 minute)
# - For production: interval=3600 (1 hour) or more
scheduler.add_job(
    generate_drift_report_background,
    "interval",
    seconds=300,  # 5 minutes
    id="drift_detection",
    name="Automatic Drift Detection",
    replace_existing=True,
)

logger.info(
    "Automatic drift detection scheduler started. Reports will be generated every 5 minutes."
)


@app.on_event("startup")
async def startup_event():
    """Start the scheduler when the app starts"""
    scheduler.start()
    logger.info("Background scheduler started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown the scheduler gracefully"""
    scheduler.shutdown()
    logger.info("Background scheduler shut down successfully")


# --- 3. API Endpoints ---


@app.post("/predict")
async def predict(features: dict):
    """
    Accepts features, makes prediction, logs data for monitoring.
    Expected keys: sepal length (cm), sepal width (cm), petal length (cm), petal width (cm)
    """
    try:
        # Convert input to DataFrame
        input_df = pd.DataFrame([features])

        # Predict
        prediction_idx = model.predict(input_df)[0]
        prediction_class = target_names[prediction_idx]

        # Log for monitoring (Append to our memory list)
        # We add the prediction to the input features to track concept drift if we had labels
        log_entry = features.copy()
        log_entry["prediction"] = int(prediction_idx)
        # TODO: In a real app, we would use a database to store the production data.
        production_data.append(log_entry)

        # Keep only last 500 items to manage memory
        if len(production_data) > 500:
            production_data.pop(0)

        logger.debug(
            f"Prediction made. Total production data points: {len(production_data)}"
        )
        return {"class": prediction_class, "class_id": int(prediction_idx)}
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return {"error": str(e)}


# TODO: In a real production app, we would not need this endpoint. Instead, we would use Airflow or Celery to generate the reports.
@app.get("/monitor/generate_report")
async def generate_report():
    """
    Manually triggers drift report generation (OPTIONAL - reports are generated automatically every 5 minutes).
    Use this endpoint if you want an immediate on-demand report.
    """
    logger.info(
        f"[MANUAL] Report generation requested. Production data points: {len(production_data)}"
    )

    if len(production_data) < 10:
        logger.warning("[MANUAL] Not enough data to generate report")
        return {
            "message": "Not enough data to generate report. Run the simulator first.",
            "current_data_points": len(production_data),
            "note": "Automatic reports are generated every 5 minutes once enough data is collected.",
        }

    try:
        # Create DataFrame from current logs
        df_current = pd.DataFrame(production_data)
        logger.info(f"[MANUAL] Current data shape: {df_current.shape}")

        # Feature list for drift detection
        features_list = [
            "sepal length (cm)",
            "sepal width (cm)",
            "petal length (cm)",
            "petal width (cm)",
        ]

        # Generate Report
        logger.info("[MANUAL] Generating Evidently report...")
        report = Report([DataDriftPreset()])

        my_eval = report.run(
            reference_data=df_reference, current_data=df_current[features_list]
        )

        # Save report with timestamp
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(reports_dir, f"drift_report_manual_{timestamp}.html")

        # Also save as latest
        latest_report_path = os.path.join(reports_dir, "drift_report_latest.html")

        logger.info(f"[MANUAL] Saving report to {report_path}")
        my_eval.save_html(report_path)
        my_eval.save_html(latest_report_path)

        # Verify the file was created
        if os.path.exists(report_path):
            file_size = os.path.getsize(report_path)
            logger.info(f"[MANUAL] Report successfully saved. Size: {file_size} bytes")
        else:
            logger.error(f"[MANUAL] Report file was not created at {report_path}")

        return {
            "message": "Report generated successfully (manual trigger)",
            "latest_report_url": "http://localhost:8080/drift_report_latest.html",
            "timestamped_report": f"http://localhost:8080/drift_report_manual_{timestamp}.html",
            "data_points_analyzed": len(production_data),
            "report_path": report_path,
            "note": "Automatic reports are generated every 5 minutes and saved with timestamps.",
        }
    except Exception as e:
        logger.error(f"[MANUAL] Error generating report: {str(e)}")
        return {"error": str(e)}


# TODO: In a real production app, we would not need this endpoint. Instead, we would use Airflow or Celery to generate the reports.
@app.get("/monitor/status")
async def monitor_status():
    """
    Get the status of automatic drift monitoring.
    """
    import glob

    reports_dir = "reports"
    report_files = []

    if os.path.exists(reports_dir):
        # Get all drift reports sorted by modification time (newest first)
        report_pattern = os.path.join(reports_dir, "drift_report_*.html")
        files = glob.glob(report_pattern)
        files.sort(key=os.path.getmtime, reverse=True)

        for file in files[:10]:  # Show last 10 reports
            file_name = os.path.basename(file)
            file_size = os.path.getsize(file)
            mod_time = datetime.fromtimestamp(os.path.getmtime(file)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            report_files.append(
                {
                    "name": file_name,
                    "url": f"http://localhost:8080/{file_name}",
                    "size_bytes": file_size,
                    "modified": mod_time,
                }
            )

    # Get scheduler job info
    job = scheduler.get_job("drift_detection")
    next_run = None
    if job:
        next_run = (
            job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
            if job.next_run_time
            else None
        )

    return {
        "automatic_detection": "enabled",
        "interval_seconds": 300,
        "interval_description": "5 minutes",
        "next_scheduled_run": next_run,
        "current_data_points": len(production_data),
        "minimum_data_points_required": 10,
        "ready_for_detection": len(production_data) >= 10,
        "recent_reports": report_files,
        "latest_report_url": (
            "http://localhost:8080/drift_report_latest.html" if report_files else None
        ),
    }


# TODO: In a real production app, we would not need this endpoint. Instead, we would use Airflow or Celery to generate the reports.
@app.post("/monitor/trigger_now")
async def trigger_drift_detection_now():
    """
    Immediately trigger the automatic drift detection (bypasses the schedule).
    Useful for testing or when you need an immediate report.
    """
    logger.info("[TRIGGER] Immediate drift detection requested")
    generate_drift_report_background()
    return {
        "message": "Drift detection triggered successfully",
        "data_points_analyzed": len(production_data),
        "latest_report_url": "http://localhost:8080/drift_report_latest.html",
    }


@app.get("/health")
def health():
    return {"status": "ok", "automatic_drift_detection": "enabled"}
