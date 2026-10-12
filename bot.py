import os
import json
from flask import Flask, request, jsonify
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Konfigurasi Google Sheets API menggunakan Service Account
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

def get_sheets_data():
    try:
        # Jika file credentials.json ada di folder
        if os.path.exists('credentials.json'):
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPE)
        else:
            # Mengambil dari Environment Variable Render jika diset via teks JSON
            creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
            creds_dict = json.loads(creds_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)

        client = gspread.authorize(creds)
        
        # Buka spreadsheet berdasarkan nama file di Google Drive anda
        sheet = client.open("Manpower_Cost").sheet1  # Mengambil sheet pertama
        
        # Ambil semua data dan ubah menjadi DataFrame Pandas
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        print(f"Gagal koneksi ke Google Sheets: {e}")
        return None

@app.route('/', methods=['GET'])
def home():
    return "Bot WhatsApp Manpower Cost (Secure Google Sheets) Aktif!", 200

@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Tiada data diterima"}), 400

    message = data.get('message', '').strip().lower()
    
    # Ambil data terbaru langsung dari Google Sheets setiap kali ada pesan masuk
    df = get_sheets_data()
    if df is None or df.empty:
        return jsonify({"status": "success", "reply": "Maaf, gagal mengambil data dari Google Sheets."})

    response_text = "Maaf, arahan tidak dikenali. Taip 'bantuan' untuk melihat menu."

    # 1. Cek Total Pembayaran Berdasarkan Bulan
    if "total" in message and "juni 2026" in message:
        # Menyesuaikan dengan nama kolom di CSV/Sheets anda
        filtered = df[df['Month'].astype(str).str.contains('2026-06')]
        total_payment = pd.to_numeric(filtered['Total Payment Amount'].astype(str).str.replace(',', ''), errors='coerce').sum()
        response_text = f"Jumlah Bayaran (Total Payment Amount) untuk bulan Jun 2026 adalah: Rp {total_payment:,.2f}"

    # 2. Cari Karyawan Berdasarkan Nama
    elif message.startswith("cari "):
        keyword = message.replace("cari ", "").strip().capitalize()
        result = df[df['Name'].astype(str).str.contains(keyword, case=False, na=False)]
        if not result.empty:
            row = result.iloc[0]
            response_text = (
                f"📋 *Maklumat Pekerja Ditemui*:\n"
                f"• Nama: {row.get('Name', '-')}\n"
                f"• Jawatan: {row.get('Job Position', '-')}\n"
                f"• Jabatan: {row.get('Department', '-')}\n"
                f"• Jumlah Bayaran: Rp {row.get('Total Payment Amount', 0)}"
            )
        else:
            response_text = f"Pekerja dengan nama '{keyword}' tidak ditemui dalam data."

    # 3. Menu Bantuan
    elif "bantuan" in message or "menu" in message:
        response_text = (
            "🤖 *Panduan Bot Manpower*:\n"
            "1. Taip *total juni 2026* untuk melihat jumlah pembayaran bulan tersebut.\n"
            "2. Taip *cari [Nama]* untuk mencari maklumat gaji pekerja."
        )

    return jsonify({
        "status": "success",
        "reply": response_text
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
