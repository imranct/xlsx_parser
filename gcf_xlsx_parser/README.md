# **GCF XLSX Parser**

This directory contains the **Google Cloud Functions (GCF)** implementation for parsing **XLSX/XLS** files. \
The function processes **simple Excel files** and offloads **complex parsing** to a **Cloud Run API**.


---


## **Overview**



* Supports **event-driven execution** via **Google Cloud Storage triggers**.
* Provides an **HTTP endpoint** for **manual execution**.
* Uses **Pandas** for **simple Excel parsing**.
* Offloads **complex Excel parsing** (with merged cells, images, tables) to **Cloud Run**.
* Saves **parsed JSON files** back into **Google Cloud Storage**.


---


## **Directory Structure**


```
gcf_xlsx_parser/
│── main.py                # Core GCF function to parse XLSX/XLS files
│── requirements.txt        # Python dependencies
│── test_gcp_xlsx_parser.py # Unit tests for the function
│── README.md               # Documentation

```



## **Deployment**


### **Deploy GCF with HTTP Trigger**

Use the following command to deploy the **HTTP-triggered function**:


```
gcloud functions deploy convert_xlsx_to_json_http \
    --runtime python312 \
    --trigger-http \
    --allow-unauthenticated \
    --entry-point convert_xlsx_to_json_http \
    --memory 8GiB \
    --timeout 300s \
    --region us-central1
```



### **Deploy GCF with Cloud Storage Event Trigger**

Use this command to deploy the **Cloud Storage-triggered function**:


```
gcloud functions deploy convert_xlsx_to_json_storage \
    --runtime python312 \
    --trigger-resource xlsx-parser-bucket \
    --trigger-event google.storage.object.finalize \
    --entry-point convert_xlsx_to_json \
    --memory 8GiB \
    --timeout 300s \
    --region us-central1
```



### **Delete Functions (For Redeployment)**

If a function needs to be redeployed with new triggers, first delete it:


```
gcloud functions delete convert_xlsx_to_json_http --region us-central1
gcloud functions delete convert_xlsx_to_json_storage --region us-central1


```



## **Function Details**


### **GCF Function: <code>convert_xlsx_to_json_storage</code></strong>



* **Trigger:** Cloud Storage (`google.storage.object.finalize`)
* **Function:** Automatically processes XLSX/XLS files uploaded to **<code>xlsx-parser-bucket</code>**.
* **Parsing Logic:**
    * If **complex structures** are detected, the file is sent to **Cloud Run API**.
    * If the file is **simple**, it is parsed using **Pandas** and stored as JSON in GCS.


### **GCF Function: <code>convert_xlsx_to_json_http</code></strong>



* **Trigger:** HTTP (`POST /convert_xlsx_to_json_http`)
* **Function:** Allows users to manually trigger the parsing process.




## **What Defines a Complex XLSX/XLS File?**

A file is considered **complex** if it contains:



1. **Merged Cells** → If values are spread across multiple rows/columns.
2. **Structured Tables** → If there are multiple distinct table regions inside a sheet.
3. **Missing or Misaligned Headers** → If column headers are not at the top or spread across multiple rows.
4. **Embedded Images/Charts** → If there are non-text elements.
5. **Highly Empty Rows & Columns** → If large parts of a sheet contain missing values.


---


## **Testing Locally**


### **1. Install Dependencies**


```
pip install -r requirements.txt
```



### **2. Run Tests**


```
pytest test_gcp_xlsx_parser.py


```



## **Configuration**



* Update **Cloud Run API URL** inside `main.py` if needed:


```
CLOUD_RUN_URL = "https://unstructured-parser-XYZ.run.app/parse"

```



* Change **Google Cloud Storage bucket name**:


```
BUCKET_NAME = "your-bucket-name"

---
```



## **Dependencies**

These dependencies are listed in `requirements.txt`:


```
pandas
requests
google-cloud-storage
Functions-framework
xlrd==2.0.1


```



## **API Usage**


### **Trigger Parsing via HTTP**

To manually trigger the function, use the following CURL command:


```
curl -X POST "https://us-central1-your-project.cloudfunctions.net/convert_xlsx_to_json_http" \
    -H "Content-Type: application/json" \
    --data '{
        "bucket": "xlsx-parser-bucket",
        "name": "file_example_XLS_5000.xls"
    }'

```



## **Known Issues & Fixes**



* **Issue:** Some XLSX files were skipping sheets or merging columns incorrectly. \
**Fix:** Improved logic for **header detection** and **empty row preservation**.
* **Issue:** GCF **memory limit exceeded** for large files. \
**Fix:** Increased **memory allocation to 8GB** & **timeout to 300s**.
* **Issue:** **Complex files (merged cells, images) were not parsed properly. \
Fix:** Offloaded complex parsing to **Cloud Run API**.


---


## **Related Repositories**



* **Cloud Run Parser** → `cloud_run_parser/` (Handles complex parsing)