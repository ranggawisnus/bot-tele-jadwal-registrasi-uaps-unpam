import requests
from bs4 import BeautifulSoup
import hashlib
import os
import sys

# KONFIGURASI
URL = "https://informatika.unpam.ac.id/info-pendaftaran-dan-jadwal-sidang-tugas-akhir"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN") # Ambil dari environment variable
CHAT_ID = os.environ.get("CHAT_ID")
STATE_FILE = "page_hash.txt"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
    except Exception as e:
        print(f"Gagal mengirim Telegram: {e}")

def get_page_content_hash():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # PENTING: Kita harus menargetkan area konten spesifik agar tidak ter-trigger
        # oleh hal sepele seperti "jumlah pengunjung" atau "jam server".
        # Berdasarkan analisis struktur umum CMS UNPAM, konten ada di tag <article> atau class tertentu.
        # Kita ambil seluruh text body untuk keamanan jika class berubah.
        
        # Mencoba mencari konten utama (Fallback logic)
        content = soup.find('article') # Struktur umum WordPress
        if not content:
            content = soup.find('div', class_='entry-content') 
        if not content:
            content = soup.body # Fallback kasar: ambil seluruh body

        # Bersihkan whitespace untuk menghindari positif palsu karena format
        clean_text = " ".join(content.get_text().split())
        
        return hashlib.md5(clean_text.encode('utf-8')).hexdigest()
    except Exception as e:
        print(f"Error scraping: {e}")
        return None

def check_for_updates():
    current_hash = get_page_content_hash()
    
    if not current_hash:
        print("Gagal mengambil data website.")
        sys.exit(1)

    # Cek hash terakhir yang disimpan
    last_hash = ""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            last_hash = f.read().strip()

    print(f"Hash Lama: {last_hash}")
    print(f"Hash Baru: {current_hash}")

    if current_hash != last_hash:
        print("PERUBAHAN TERDETEKSI!")
        # Simpan hash baru
        with open(STATE_FILE, 'w') as f:
            f.write(current_hash)
        
        # Kirim notifikasi (Hanya kirim jika ini bukan run pertama kali/file kosong)
        if last_hash != "": 
            msg = (
                f"🚨 **UPDATE TERDETEKSI!**\n\n"
                f"Halaman Info Sidang/TA Unpam telah berubah.\n"
                f"Cek segera: {URL}"
            )
            send_telegram_message(msg)
        else:
            print("Inisialisasi pertama. Hash disimpan.")
    else:
        print("Tidak ada perubahan.")

if __name__ == "__main__":
    check_for_updates()
