import os
import mlflow

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
mlflow.set_experiment("smart-energy-optimizer")

with mlflow.start_run(run_name="smoke-test"):
    mlflow.log_param("test_param", 42)
    mlflow.log_metric("test_metric", 0.95)
    with open("hello.txt", "w") as f:
        f.write("MLflow fonctionne")
    mlflow.log_artifact("hello.txt")

print("OK, va voir http://localhost:5000")