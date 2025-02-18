import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from io import BytesIO
import os
import logging
from main import GCPXLSXParser

logging.basicConfig(level=logging.DEBUG)

class TestGCPXLSXParser(unittest.TestCase):

    def setUp(self):
        """Initialize mock values for GCS interactions"""
        self.bucket_name = "xlsx-test-bucket"
        self.source_blob = "test.xlsx"
        self.destination_blob = "test.json"
        self.error_blob = "test_error.log"

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/imran_saifmalik/gcf_service_account.json"
        self.parser = GCPXLSXParser(self.bucket_name, self.source_blob, self.destination_blob, self.error_blob)

    def create_mock_xlsx(self, data):
        """Create an XLSX file in-memory with correct headers"""
        excel_file = BytesIO()
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            data.to_excel(writer, index=False)
        excel_file.seek(0)
        return excel_file.getvalue()

    def debug_check_headers(self, df):
        """Verify headers before returning DataFrame"""
        logging.debug(f"Mock XLSX headers: {df.columns.tolist()}")
        return df

    @patch("google.cloud.storage.Client")
    def test_xlsx_correct_headers(self, mock_storage_client):
        """Test with correct headers to ensure validation passes"""
        df = pd.DataFrame({"Title": ["Doc1"], "Date": ["2025-02-10"]})
        df = self.debug_check_headers(df)

        mock_blob = MagicMock()
        mock_blob.download_as_bytes.return_value = self.create_mock_xlsx(df)
        mock_storage_client().bucket().blob.return_value = mock_blob

        result = self.parser.parse()
        self.assertEqual(result, "JSON file successfully created in GCS.")

    @patch("google.cloud.storage.Client")
    def test_xlsx_missing_headers(self, mock_storage_client):
        """Test handling of an XLSX file where expected headers are missing."""
        
        # Creating a DataFrame with completely different column names
        data = pd.DataFrame({"RandomColumn1": ["Data1"], "RandomColumn2": ["Data2"]})

        mock_blob = MagicMock()
        mock_blob.download_as_bytes.return_value = self.create_mock_xlsx(data)
        mock_storage_client().bucket().blob.return_value = mock_blob

        result = self.parser.parse()

        # Since we removed strict header validation, expect SUCCESS
        self.assertEqual(result, "JSON file successfully created in GCS.")




    @patch("google.cloud.storage.Client")
    def test_xlsx_extra_columns(self, mock_storage_client):
        """Test success when required headers exist, even if extra columns are present"""
        df = pd.DataFrame({"Title": ["Doc1"], "Date": ["2025-02-10"], "ExtraColumn": ["ExtraValue"]})
        df = self.debug_check_headers(df)

        mock_blob = MagicMock()
        mock_blob.download_as_bytes.return_value = self.create_mock_xlsx(df)
        mock_storage_client().bucket().blob.return_value = mock_blob

        result = self.parser.parse()
        self.assertEqual(result, "JSON file successfully created in GCS.")

    @patch("google.cloud.storage.Client")
    def test_xlsx_special_characters(self, mock_storage_client):
        """Test handling of an XLSX file with special characters"""
        df = pd.DataFrame({"Title": ["Hello 😊"], "Date": ["2025-02-10"]})
        df = self.debug_check_headers(df)

        mock_blob = MagicMock()
        mock_blob.download_as_bytes.return_value = self.create_mock_xlsx(df)
        mock_storage_client().bucket().blob.return_value = mock_blob

        result = self.parser.parse()
        self.assertEqual(result, "JSON file successfully created in GCS.")

    @patch("google.cloud.storage.Client")
    def test_xlsx_empty_rows(self, mock_storage_client):
        """Test handling of an XLSX file with empty rows"""
        df = pd.DataFrame({"Title": ["Doc1", None], "Date": ["2025-02-10", None]})
        df = self.debug_check_headers(df)

        mock_blob = MagicMock()
        mock_blob.download_as_bytes.return_value = self.create_mock_xlsx(df)
        mock_storage_client().bucket().blob.return_value = mock_blob

        result = self.parser.parse()
        self.assertEqual(result, "JSON file successfully created in GCS.")

    @patch("google.cloud.storage.Client")
    def test_xlsx_different_date_formats(self, mock_storage_client):
        """Test handling of an XLSX file with different date formats"""
        df = pd.DataFrame({"Title": ["Doc1"], "Date": ["10-Feb-2025"]})
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
        df = self.debug_check_headers(df)

        mock_blob = MagicMock()
        mock_blob.download_as_bytes.return_value = self.create_mock_xlsx(df)
        mock_storage_client().bucket().blob.return_value = mock_blob

        result = self.parser.parse()
        self.assertEqual(result, "JSON file successfully created in GCS.")

    @patch("google.cloud.storage.Client")
    def test_xlsx_large_dataset(self, mock_storage_client):
        """Test handling of an XLSX file with a large dataset"""
        df = pd.DataFrame({"Title": ["Doc"] * 100000, "Date": ["2025-02-10"] * 100000})
        df = self.debug_check_headers(df)

        mock_blob = MagicMock()
        mock_blob.download_as_bytes.return_value = self.create_mock_xlsx(df)
        mock_storage_client().bucket().blob.return_value = mock_blob

        result = self.parser.parse()
        self.assertEqual(result, "JSON file successfully created in GCS.")

    @patch("google.cloud.storage.Client")
    def test_xlsx_merged_cells(self, mock_storage_client):
        """Test handling of an XLSX file with merged cells"""
        df = pd.DataFrame({"Title": ["Doc1"], "Date": ["2025-02-10"]})
        df = self.debug_check_headers(df)

        excel_file = BytesIO()
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, merge_cells=True)
        excel_file.seek(0)

        mock_blob = MagicMock()
        mock_blob.download_as_bytes.return_value = excel_file.getvalue()
        mock_storage_client().bucket().blob.return_value = mock_blob

        result = self.parser.parse()
        self.assertEqual(result, "JSON file successfully created in GCS.")

if __name__ == "__main__":
    unittest.main()
