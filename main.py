from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import json
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

app = FastAPI(title="Saham Analytics API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# FUNGSI BANTUAN: BACA GDRIVE LANGSUNG
# ==========================================
def get_saham_data():
    # 1. Ambil kunci rahasia dari brankas Vercel
    creds_str = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_str:
        raise Exception("Kredensial tidak ditemukan! Pastikan GOOGLE_CREDENTIALS sudah diisi di Vercel.")

    # 2. Login ke Google Drive
    creds_info = json.loads(creds_str)
    credentials = service_account.Credentials.from_service_account_info(
        creds_info, scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    service = build('drive', 'v3', credentials=credentials)

    # 3. Cari file CSV di dalam Folder Bapak (ID Folder dari link Bapak)
    folder_id = '1hX2jwUrAgi4Fr8xkcFWjCW6vbk6lsIlP'
    query = f"'{folder_id}' in parents and name='Shareholder_1Persen_Processed.csv' and trashed=false"
    results = service.files().list(q=query, fields="files(id)").execute()
    items = results.get('files', [])

    if not items:
        raise Exception("File CSV tidak ditemukan di dalam folder Google Drive tersebut!")

    file_id = items[0]['id']

    # 4. Download file ke memori (tanpa simpan di harddisk Vercel agar cepat)
    request = service.files().get_media(fileId=file_id)
    downloaded = io.BytesIO()
    downloader = MediaIoBaseDownload(downloaded, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()

    downloaded.seek(0)
    
    # 5. Ubah jadi Pandas DataFrame
    df = pd.read_csv(downloaded)
    return df

# ==========================================
# ENDPOINTS API (Rute Data)
# ==========================================

@app.get("/")
def root():
    return {"message": "API Backend Saham Aktif! Berhasil terkoneksi ke Google Drive."}

@app.get("/api/saham/summary")
def get_summary():
    try:
        df = get_saham_data()
        # Untuk preview, kita tampilkan 100 baris pertama agar loading cepat
        result = df.head(100).to_dict(orient="records")
        return {
            "status": "success", 
            "message": "Data asli dari Google Drive berhasil ditarik!",
            "total_rows_in_database": len(df), 
            "data": result
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/saham/hsc-alert")
def get_hsc_alert():
    try:
        df = get_saham_data()
        # Logika Deteksi HSC Asli
        hsc_grouped = df.groupby("SHARE_CODE")["PERCENTAGE"].sum().reset_index()
        hsc_danger = hsc_grouped[hsc_grouped["PERCENTAGE"] > 85.0]
        
        return {
            "status": "success", 
            "hsc_detected": len(hsc_danger), 
            "data": hsc_danger.to_dict(orient="records")
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
