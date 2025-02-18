import os
import json
import logging
import requests
import pandas as pd
from flask import Flask, request, jsonify
from google.cloud import storage
import functions_framework
from io import BytesIO

# Cloud Run Unstructured Parser URL
CLOUD_RUN_URL = "https://unstructured-parser-258481069493.us-central1.run.app/parse"

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    filename="main_parser.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Google Cloud Storage client
storage_client = storage.Client()

class GCPXLSXParser:
    def __init__(self, bucket_name: str, source_blob: str, destination_blob: str, error_blob: str):
        self.bucket = storage_client.bucket(bucket_name)
        self.source_blob = source_blob
        self.destination_blob = destination_blob
        self.error_blob = error_blob

    def json_serializer(self, obj):
        if isinstance(obj, pd.Timestamp):
            return obj.strftime("%Y-%m-%d")
        if pd.isna(obj):
            return None
        return str(obj)

    def detect_complexity(self, xls):
        """Checks if Excel contains complex structures (merged cells, structured tables, images)."""
        for sheet_name in xls.sheet_names:
            df = xls.parse(sheet_name, dtype=str, header=None)
            if df.isna().sum().sum() > 0:
                logging.info(f"Complexity detected in sheet '{sheet_name}': Merged/empty cells.")
                return True
            if sheet_name.lower() in ["overview", "metadata schema", "report"]:
                logging.info(f"Complexity detected in sheet '{sheet_name}': Possible structured format.")
                return True
        return False

    def log_error(self, message):
        """Logs errors to a separate GCS file."""
        error_blob = self.bucket.blob(self.error_blob)
        existing_log = ""
        if error_blob.exists():
            existing_log = error_blob.download_as_text()
        error_blob.upload_from_string(existing_log + message + '\n', content_type='text/plain')
        logging.error(message)

    def forward_to_cloud_run(self):
        """Forwards the request to Cloud Run for complex Excel processing."""
        logging.info(f"Forwarding request to Cloud Run: {CLOUD_RUN_URL}")

        payload = {
            "bucket_name": self.bucket.name,
            "file_name": self.source_blob
        }

        try:
            response = requests.post(CLOUD_RUN_URL, json=payload, timeout=300)
            response_data = response.json()

            if response.status_code == 200:
                logging.info("Successfully processed complex Excel via Cloud Run.")
                return response_data
            else:
                error_msg = f"Cloud Run failed: {response_data.get('error', 'Unknown error')}"
                logging.error(error_msg)
                return {"error": error_msg}

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to communicate with Cloud Run: {str(e)}"
            logging.error(error_msg)
            return {"error": error_msg}

    def parse(self) -> str:
        """Parses the XLSX/XLS file, handles errors, and switches to Cloud Run when needed."""
        try:
            blob = self.bucket.blob(self.source_blob)
            if not blob.exists():
                raise ValueError(f"File {self.source_blob} does not exist in bucket.")

            excel_data = blob.download_as_bytes()
            if not excel_data:
                raise ValueError("Downloaded file is empty.")

            file_format = "xls" if self.source_blob.endswith(".xls") else "xlsx"

            # Ensure xlrd==1.2.0 for XLS
            if file_format == "xls":
                try:
                    xls = pd.ExcelFile(BytesIO(excel_data), engine="xlrd")
                except Exception as e:
                    raise ValueError(f"Failed to read .xls file. Ensure xlrd==1.2.0 is installed. Error: {str(e)}")
            else:
                try:
                    xls = pd.ExcelFile(BytesIO(excel_data), engine="openpyxl")
                except Exception as e:
                    raise ValueError(f"Invalid .xlsx file format: {str(e)}")

            # Forward complex files to Cloud Run
            if self.detect_complexity(xls):
                cloud_run_response = self.forward_to_cloud_run()
                if "error" not in cloud_run_response:
                    return cloud_run_response  # Cloud Run succeeded
                logging.warning("Cloud Run processing failed, falling back to normal parsing.")

            # Process simple Excel files
            data_dict = {}
            for sheet_name in xls.sheet_names:
                try:
                    df = xls.parse(sheet_name, dtype=str, header=0)
                    df.dropna(axis=1, how="all", inplace=True)
                    df.dropna(axis=0, how="all", inplace=True)

                    if df.empty:
                        logging.warning(f"Sheet '{sheet_name}' is empty. Skipping.")
                        continue

                    data_dict[sheet_name] = df.to_dict(orient="records")

                except Exception as e:
                    error_message = f"Error processing sheet '{sheet_name}': {str(e)}"
                    self.log_error(error_message)
                    logging.error(error_message)
                    return "Failed to process XLSX file."

            if not data_dict:
                raise ValueError("No valid data found in the Excel file.")

            json_blob = self.bucket.blob(self.destination_blob)
            json_blob.upload_from_string(json.dumps(data_dict, indent=4, default=self.json_serializer),
                                         content_type='application/json')
            logging.info("JSON file successfully created in GCS.")

            return "JSON file successfully created in GCS."

        except Exception as e:
            error_message = f"Error processing file {self.source_blob}: {str(e)}"
            self.log_error(error_message)
            logging.error(error_message)
            return "Failed to process XLSX file."

@functions_framework.cloud_event
def convert_xlsx_to_json(cloud_event):
    """Triggered when an XLS/XLSX file is uploaded to GCS."""
    try:
        data = cloud_event.data
        bucket_name = data["bucket"]
        source_blob = data["name"]
        if not (source_blob.endswith(".xlsx") or source_blob.endswith(".xls")):
            logging.warning(f"Ignoring non-Excel file: {source_blob}")
            return "Ignoring non-Excel file."
        parser = GCPXLSXParser(bucket_name, source_blob, source_blob.replace(".xlsx", ".json").replace(".xls", ".json"), source_blob.replace(".xlsx", "_error.log"))
        return parser.parse()
    except Exception as e:
        logging.error(f"Critical error in function execution: {str(e)}")
        return "Function execution failed."

@functions_framework.http
def convert_xlsx_to_json_http(request):
    """Handles HTTP request for XLS/XLSX file parsing."""
    try:
        request_json = request.get_json(silent=True)
        if not request_json:
            return jsonify({"error": "Invalid JSON payload"}), 400

        bucket_name = request_json.get("bucket")
        source_blob = request_json.get("name")

        if not bucket_name or not source_blob:
            return jsonify({"error": "Missing required parameters"}), 400

        parser = GCPXLSXParser(
            bucket_name, source_blob,
            source_blob.replace(".xlsx", ".json").replace(".xls", ".json"),
            source_blob.replace(".xlsx", "_error.log").replace(".xls", "_error.log")
        )

        response = parser.parse()
        return jsonify({"message": response})

    except Exception as e:
        logging.error(f"Error processing HTTP request: {str(e)}")
        return jsonify({"error": str(e)}), 500
