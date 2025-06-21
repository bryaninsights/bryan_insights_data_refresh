import requests
import pandas as pd
import re
import json
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# -------------------------------
# Google Drive Authentication
# -------------------------------
creds_path = "gdrive_creds.json"
with open(creds_path, "w") as f:
    f.write(os.environ["GDRIVE_CREDENTIALS"])  # Add this as a GitHub Secret

gauth = GoogleAuth()
gauth.LoadServiceConfigFile(creds_path)
gauth.ServiceAuth()
drive = GoogleDrive(gauth)

# -------------------------------
# Brilliant Assessments API
# -------------------------------
API_KEY = "11051A9A-3AA1-4E07-9BE0-F5BFBFDA9870"
HEADERS = {
    "APIKey": API_KEY,
    "Content-Type": "application/json"
}

url = "https://api.brilliantassessments.com/api/assessmentresponse/getchanges"
response = requests.get(url, headers=HEADERS)

if response.status_code != 200:
    print(f" Failed to fetch response IDs: {response.status_code} {response.text}")
    exit()

response_ids = response.json().get("ResponseIds", [])
print(f" Found {len(response_ids)} response IDs")

records = []
for rid in response_ids[:]:  # Can remove [:] to fetch all
    detail_url = f"https://api.brilliantassessments.com/api/assessmentresponse/getassessmentresponse/{rid}"
    res = requests.get(detail_url, headers=HEADERS)

    if res.status_code != 200:
        print(f" Skipped {rid} — {res.status_code}")
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
# Convert to DataFrame
# -------------------------------
df = pd.DataFrame(records)
df.columns = [re.sub(r'[^\w\s\)\]]+$', '', col.strip()) for col in df.columns]

print(df.head())
df.to_csv("assessment_data.csv", index=False)

# -------------------------------
# Upload to Google Drive
# -------------------------------
gfile = drive.CreateFile({'title': "assessment_data.csv"})
gfile.SetContentFile("assessment_data.csv")
gfile.Upload()
print("✅ Uploaded to Google Drive.")
