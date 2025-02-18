### **📄 XLSX Parser - Google Cloud Functions & Cloud Run**

**A robust Excel (XLS/XLSX) parsing solution using Google Cloud Functions for simple files and Cloud Run for complex structured files.**



---


## **📌 Overview**

This project provides an end-to-end solution for parsing Excel spreadsheets efficiently:



* **Google Cloud Functions (GCF)** handles basic XLSX/XLS files with simple structures.
* **Cloud Run API** processes complex files containing embedded tables, merged cells, and images.
* The system automatically determines which parser to use based on file complexity.


### **🔍 Why This Approach?**



* **GCF has a 512MB function size limit**, making it unsuitable for large dependencies.
* **Unstructured Parser**, required for handling complex Excel files, exceeds this limit.
* **Cloud Run** allows unlimited package sizes and runs a dedicated API for complex parsing.


---


## **📂 Repository Structure**


```
xlsx-parser/
├── gcf_xlsx_parser/      # Google Cloud Functions code
│   ├── main.py           # GCF function to parse simple Excel files
│   ├── requirements.txt  # Python dependencies for GCF
│   ├── README.md
├── cloud_run_parser/     # Cloud Run API for complex parsing
│   ├── main.py           # Flask API for parsing complex Excel files
│   ├── Dockerfile        # Docker setup for Cloud Run deployment
│   ├── requirements.txt  # Python dependencies for Cloud Run
│   ├── README.md
├── README.md             # Root README explaining both components
└── .gitignore            # Ignoring unnecessary files (logs, cache, venv, etc.)


```



## **🚀 Deployment**


### **1️⃣ Google Cloud Functions (GCF)**

Deploy **GCF for simple Excel parsing** using:


```
gcloud functions deploy convert_xlsx_to_json_http \
    --runtime python312 \
    --trigger-http \
    --allow-unauthenticated \
    --entry-point convert_xlsx_to_json_http \
    --memory 8GiB \
    --timeout 300s \
    --region us-central1

gcloud functions deploy convert_xlsx_to_json_storage \
    --runtime python312 \
    --trigger-resource xlsx-parser-bucket \
    --trigger-event google.storage.object.finalize \
    --entry-point convert_xlsx_to_json \
    --memory 8GiB \
    --timeout 300s \
    --region us-central1
```



### **2️⃣ Cloud Run (Complex Parsing)**

Deploy **Cloud Run API for complex parsing** using:


```
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/xlsx-parser
gcloud run deploy xlsx-parser \
    --image gcr.io/YOUR_PROJECT_ID/xlsx-parser \
    --region us-central1 --platform managed --allow-unauthenticated --memory 8GiB

```



## **📌 Usage**


### **1️⃣ Trigger via HTTP (GCF)**

Use the HTTP function for on-demand parsing:


```
curl -X POST "https://us-central1-YOUR_PROJECT_ID.cloudfunctions.net/convert_xlsx_to_json_http" \
    -H "Content-Type: application/json" \
    --data '{
        "bucket": "xlsx-parser-bucket",
        "name": "file_example_XLS_5000.xls"
    }'
```



### **2️⃣ Automatic Cloud Storage Trigger**

Simply upload an Excel file (`.xls` or `.xlsx`) to **<code>xlsx-parser-bucket</code>**, and the GCF function will process it automatically.


### **3️⃣ Complex Parsing via Cloud Run**

If a file is detected as complex, it is forwarded to **Cloud Run** API:


```
curl -X POST "https://YOUR_CLOUD_RUN_URL/parse" \
    -H "Content-Type: application/json" \
    --data '{
        "bucket_name": "xlsx-parser-bucket",
        "file_name": "complex_excel.xlsx"
    }'

```



## **⚙️ Development & Testing**


### **1️⃣ Clone the Repository**


```
git clone https://github.com/imranct/xlsx_parser.git
cd xlsx-parser
```



### **2️⃣ Install Dependencies (Local Testing)**


#### **Google Cloud Functions:**


```
cd gcf_xlsx_parser
pip install -r requirements.txt
```



#### **Cloud Run:**


```
cd cloud_run_parser
pip install -r requirements.txt
```



### **3️⃣ Run Cloud Run API Locally**


```
cd cloud_run_parser
python main.py
```


Access API locally at: `http://127.0.0.1:8080/parse`


---


## **📌 Debugging & Logs**

Check logs for GCF:


```
gcloud functions logs read convert_xlsx_to_json_storage --limit=50 --format=json | jq '.[].log'
```


Check logs for Cloud Run:


```
gcloud run services logs read xlsx-parser --region us-central1 --limit=50

```



## **🗑️ Deleting & Redeploying**

If you need to delete the function and redeploy:


```
gcloud functions delete convert_xlsx_to_json_http --region us-central1
gcloud functions delete convert_xlsx_to_json_storage --region us-central1
```


Then, redeploy using the deployment commands above.


---


## **📌 Future Enhancements**



* Add support for Google Sheets integration.
* Optimize memory management for large files in Cloud Run.
* Implement better error handling and logging for debugging.