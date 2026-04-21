from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

# Inisialisasi Aplikasi FastAPI
app = FastAPI(title="Saham Analytics API", version="1.0")

# Atur CORS (Sangat penting agar Frontend Next.js/Vercel bisa akses API ini)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Nanti bisa diganti dengan URL Vercel Bapak agar lebih aman
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# FUNGSI BANTUAN: AMBIL DATA DARI GDRIVE
# ==========================================
def get_saham_data():
    """
    Fungsi ini nantinya akan membaca kredensial dari Service Account,
    mendownload file CSV dari GDrive, dan mengubahnya menjadi DataFrame Pandas.
    Untuk testing awal, kita kembalikan DataFrame kosong.
    """
    # TODO: Integrasi Google Drive Service Account akan kita taruh di sini
    
    # Simulasi data sementara (Mock Data) untuk memastikan API menyala
    data = {
        "DATE": ["27-Feb-2026", "27-Feb-2026"],
        "SHARE_CODE": ["AADI", "BBCA"],
        "INVESTOR_NAME": ["ADARO STRATEGIC", "PT DWIMURIA"],
        "PERCENTAGE": [41.1, 54.94],
        "Sector": ["Energy", "Financials"],
        "Free Float": [18.8, 43.0]
    }
    return pd.DataFrame(data)

# ==========================================
# ENDPOINTS API (Rute Data yang bisa diakses web)
# ==========================================

@app.get("/")
def root():
    return {"message": "API Backend Saham Aktif! Mesin siap digunakan."}

@app.get("/api/saham/summary")
def get_summary():
    """
    Endpoint untuk mengambil ringkasan data saham.
    """
    df = get_saham_data()
    
    # Convert DataFrame ke format JSON (Dictionary) agar bisa dibaca web
    result = df.to_dict(orient="records")
    return {"status": "success", "total_rows": len(df), "data": result}

@app.get("/api/saham/hsc-alert")
def get_hsc_alert():
    """
    Endpoint khusus untuk logika Dashboard: Menghitung saham yang rawan HSC (>85% dikuasai paus)
    """
    df = get_saham_data()
    
    # Logika Pandas: Kelompokkan berdasarkan kode saham, jumlahkan persentase paus
    hsc_grouped = df.groupby("SHARE_CODE")["PERCENTAGE"].sum().reset_index()
    
    # Filter yang totalnya di atas 85%
    hsc_danger = hsc_grouped[hsc_grouped["PERCENTAGE"] > 85.0]
    
    return {
        "status": "success", 
        "hsc_detected": len(hsc_danger), 
        "data": hsc_danger.to_dict(orient="records")
    }

# Hanya untuk running lokal di komputer Bapak
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
