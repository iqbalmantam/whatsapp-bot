from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

# Load data CSV saat server pertama kali jalan
CSV_FILE = 'Manpower_Cost.csv'
df = pd.read_csv(CSV_FILE)

@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    # Menerima pesan masuk dari WhatsApp Gateway (Contoh format umum)
    data = request.json
    sender = data.get('sender', '') # Nomor pengirim
    message = data.get('message', '').strip().lower() # Isi pesan
    
    response_text = "Maaf, perintah tidak dikenali."

    # Contoh Logika Sederhana Berdasarkan Pertanyaan WhatsApp
    if "total" in message and "juni 2026" in message:
        # Filter data bulan Juni 2026 (contoh)
        filtered = df[df['Month'] == '2026-06-01']
        total_payment = filtered['Total Payment Amount'].sum()
        response_text = f"Total Payment Amount untuk bulan Juni 2026 adalah: Rp {total_payment:,.2f}"
        
    elif "cari" in message or "nama" in message:
        # Contoh pencarian nama karyawan
        parts = message.split(" ")
        if len(parts) > 1:
            keyword = parts[1].capitalize()
            result = df[df['Name'].str.contains(keyword, na=False)]
            if not result.empty:
                row = result.iloc[0]
                response_text = (
                    f"Ditemukan:\n"
                    f"Nama: {row['Name']}\n"
                    f"Jabatan: {row['Job Position']}\n"
                    f"Total Payment: Rp {row['Total Payment Amount']:,.2f}"
                )
            else:
                response_text = f"Karyawan dengan nama '{keyword}' tidak ditemukan."

    # Kirim balik respons ke WhatsApp (sesuaikan dengan API Provider Anda, misal Fonnte/Wablas)
    # Contoh kirim via Fonnte API:
    # requests.post('https://api.fonnte.com/send', data={'target': sender, 'message': response_text}, headers={'Authorization': 'TOKEN_ANDA'})

    return jsonify({"status": "success", "reply": response_text})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
