import os
import json
import requests
import pandas as pd
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# -------------------------------
# 1. AUTHENTICATE GOOGLE DRIVE
# -------------------------------
# Save service account JSON credentials from environment variable
with open("service_account.json", "w") as f:
    f.write(os.environ["GDRIVE_CREDENTIALS"])  # Must be set in GitHub Secrets

# Load credentials
creds = service_account.Credentials.from_service_account_file("service_account.json")
drive_service = build("drive", "v3", credentials=creds)

# -------------------------------
# 2. FETCH DATA FROM API
# -------------------------------
API_KEY = "11051A9A-3AA1-4E07-9BE0-F5BFBFDA9870"
HEADERS = {
    "APIKey": API_KEY,
    "Content-Type": "application/json"
}

url = "https://api.brilliantassessments.com/api/assessmentresponse/getchanges"
response = requests.get(url, headers=HEADERS)

if response.status_code != 200:
    print(f"❌ Failed to fetch response IDs: {response.status_code} {response.text}")
    exit()

response_ids = response.json().get("ResponseIds", [])
print(f"✅ Found {len(response_ids)} response IDs")

records = []
for rid in response_ids[:]:  # Can remove [:] to fetch all
    detail_url = f"https://api.brilliantassessments.com/api/assessmentresponse/getassessmentresponse/{rid}"
    res = requests.get(detail_url, headers=HEADERS)

    if res.status_code != 200:
        print(f"⚠️ Skipped {rid} — {res.status_code}")
        continue

    data = res.json()
    row = {
        "ResponseId": rid,
        "Email": data.get("Email"),
        "First Name": data.get("FirstName"),
        "Last Name": data.get("LastName"),
        "Completion Date": data.get("CompletionDate"),
        "Business Name": data.get("BusinessName"),
        "Status": data.get("Status"),
        "Organizational Performance Rating": data.get("Rating", {}).get("Score")
    }

    for seg in data.get("SegmentationRatings", []):
        name = seg.get("SegmentationName")
        score = seg.get("Score")
        if name:
            row[name] = score

    records.append(row)

# -------------------------------
# 3. SAVE AS CSV
# -------------------------------
df = pd.DataFrame(records)
df.columns = [re.sub(r'[^\w\s\)\]]+$', '', col.strip()) for col in df.columns]
df.to_csv("assessment_data.csv", index=False)
print("✅ Saved to assessment_data.csv")

# -------------------------------
# 4. UPLOAD TO GOOGLE DRIVE
# -------------------------------
file_metadata = {"name": "assessment_data.csv"}
media = MediaFileUpload("assessment_data.csv", mimetype="text/csv")
file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
print(f"✅ Uploaded to Google Drive with ID: {file.get('id')}")
