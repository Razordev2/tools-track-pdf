#!/usr/bin/env python3
"""
PDF TRACKER - Buat PDF dengan kemampuan tracking
Cocok untuk Kali Linux
"""

import os
import sys
import json
import time
import socket
import hashlib
import requests
import qrcode
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
from PIL import Image
from cryptography.fernet import Fernet

class PDFTracker:
    """
    Kelas untuk membuat PDF yang bisa dilacak
    """
    
    def __init__(self, server_url="http://yourserver.com/track"):
        self.server_url = server_url
        self.tracking_data = {}
        self.log_file = "tracking_log.txt"
        
    def generate_user_id(self, user_info):
        """Buat ID unik berdasarkan info user"""
        data = f"{user_info['email']}{user_info['ip']}{time.time()}"
        return hashlib.md5(data.encode()).hexdigest()[:16]
    
    def create_watermark_text(self, user_info):
        """Buat teks watermark yang unik per user"""
        watermark = f"""
        ═══════════════════════════════════════
        DOKUMEN UNTUK: {user_info['name']}
        EMAIL: {user_info['email']}
        IP: {user_info['ip']}
        TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        ID: {self.generate_user_id(user_info)}
        ═══════════════════════════════════════
        """
        return watermark
    
    def create_qr_tracker(self, user_info):
        """Buat QR code yang berisi data tracking"""
        data = {
            'user': user_info['email'],
            'ip': user_info['ip'],
            'time': str(datetime.now()),
            'doc_id': self.generate_user_id(user_info)
        }
        
        # Konversi ke JSON
        json_data = json.dumps(data)
        
        # Buat QR code
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=5
        )
        qr.add_data(json_data)
        qr.make(fit=True)
        
        # Simpan sebagai gambar
        img = qr.make_image(fill_color="black", back_color="white")
        qr_path = f"/tmp/qr_{user_info['email']}.png"
        img.save(qr_path)
        
        return qr_path
    
    def embed_json_metadata(self, pdf_path, user_info):
        """Sisipkan JSON metadata ke PDF"""
        # Ini menggunakan PyPDF2 untuk menyisipkan metadata
        from PyPDF2 import PdfReader, PdfWriter
        
        metadata = {
            '/Tracking-ID': self.generate_user_id(user_info),
            '/User-Email': user_info['email'],
            '/User-IP': user_info['ip'],
            '/Download-Time': str(datetime.now()),
            '/Server-URL': self.server_url
        }
        
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
        
        # Tambahkan metadata
        writer.add_metadata(metadata)
        
        # Simpan dengan metadata baru
        output_path = pdf_path.replace('.pdf', '_tracked.pdf')
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        return output_path
    
    def create_tracked_pdf(self, output_file, content_text, user_info):
        """
        Membuat PDF dengan tracking capability
        
        Args:
            output_file: Nama file output
            content_text: Isi teks PDF
            user_info: Dict berisi info user (name, email, ip)
        """
        
        # Buat PDF dasar
        c = canvas.Canvas(output_file, pagesize=A4)
        width, height = A4
        
        # Tambahkan judul
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "DOKUMEN TERLACAK - CONFIDENTIAL")
        
        # Tambahkan teks watermark di background (transparan)
        c.saveState()
        c.setFillColorRGB(0.9, 0.9, 0.9)  # Abu-abu muda
        c.setFont("Helvetica", 40)
        c.translate(width/2, height/2)
        c.rotate(45)
        c.drawCentredString(0, 0, "TRACKED DOCUMENT")
        c.restoreState()
        
        # Tambahkan teks konten
        c.setFont("Helvetica", 12)
        y_position = height - 100
        
        # Split teks jadi beberapa baris
        lines = content_text.split('\n')
        for line in lines:
            if y_position < 50:
                c.showPage()
                y_position = height - 50
            c.drawString(50, y_position, line)
            y_position -= 20
        
        # Tambahkan watermark user di footer (per halaman)
        watermark_text = self.create_watermark_text(user_info)
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)  # Abu-abu gelap
        c.drawString(50, 30, watermark_text[:100])  # Potong biar muat
        
        # Buat QR code tracker
        qr_path = self.create_qr_tracker(user_info)
        
        # Sisipkan QR code di halaman terakhir
        c.showPage()
        c.drawImage(qr_path, 50, height - 200, width=150, height=150)
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 220, "Scan QR untuk verifikasi")
        c.drawString(50, height - 240, f"ID: {self.generate_user_id(user_info)}")
        
        # Simpan PDF
        c.save()
        
        # Bersihkan file temporary
        os.remove(qr_path)
        
        # Sisipkan JSON metadata
        final_pdf = self.embed_json_metadata(output_file, user_info)
        
        # Simpan tracking data ke log
        self.save_tracking_log(user_info, output_file)
        
        # Kirim notifikasi ke server (jika online)
        self.send_tracking_notification(user_info, output_file)
        
        print(f"\n✅ PDF TRACKING BERHASIL DIBUAT!")
        print(f"📁 File: {final_pdf}")
        print(f"👤 Untuk: {user_info['name']} <{user_info['email']}>")
        print(f"📍 IP: {user_info['ip']}")
        print(f"🆔 Tracking ID: {self.generate_user_id(user_info)}")
        
        return final_pdf
    
    def save_tracking_log(self, user_info, pdf_file):
        """Simpan log tracking ke file"""
        log_entry = {
            'time': str(datetime.now()),
            'user': user_info,
            'pdf': pdf_file,
            'tracking_id': self.generate_user_id(user_info)
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def send_tracking_notification(self, user_info, pdf_file):
        """Kirim notifikasi ke server tracking"""
        try:
            data = {
                'event': 'pdf_generated',
                'user': user_info,
                'pdf': pdf_file,
                'time': str(datetime.now())
            }
            
            # Kirim ke server (jika ada)
            if self.server_url:
                response = requests.post(self.server_url, json=data, timeout=5)
                print(f"📡 Notifikasi terkirim ke server: {response.status_code}")
        except:
            print("⚠️ Gagal mengirim notifikasi ke server (offline mode)")

class PDFTrackerServer:
    """
    Server sederhana untuk menerima tracking data
    Jalankan di terminal terpisah
    """
    
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.setup_routes()
    
    def setup_routes(self):
        from flask import Flask, request, jsonify
        
        @self.app.route('/track', methods=['POST'])
        def track_pdf():
            data = request.json
            print(f"\n🔔 PDF TRACKING EVENT!")
            print(f"User: {data.get('user', {}).get('email')}")
            print(f"Event: {data.get('event')}")
            print(f"Time: {data.get('time')}")
            
            # Simpan ke file log
            with open('server_log.txt', 'a') as f:
                f.write(json.dumps(data) + '\n')
            
            return jsonify({'status': 'ok', 'message': 'Tracked'})
        
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({'status': 'alive', 'time': str(datetime.now())})
    
    def run(self):
        print(f"🚀 Tracking server running on http://{self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port)

def get_local_ip():
    """Dapatkan IP lokal komputer"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def main():
    """Program utama"""
    print("""
    ╔══════════════════════════════════════╗
    ║   PDF TRACKING TOOLS - KALI LINUX    ║
    ║      Buat PDF dengan kemampuan lacak  ║
    ╚══════════════════════════════════════╝
    """)
    
    # Pilih mode
    print("Pilih mode:")
    print("1. Generate PDF dengan tracking")
    print("2. Jalankan tracking server")
    print("3. Lihat log tracking")
    print("4. Keluar")
    
    choice = input("\nPilihan [1-4]: ").strip()
    
    if choice == '1':
        # Mode generate PDF
        tracker = PDFTracker(server_url="http://localhost:5000/track")
        
        # Input data user
        print("\n📝 MASUKKAN DATA USER:")
        user_info = {}
        user_info['name'] = input("Nama User: ").strip()
        user_info['email'] = input("Email User: ").strip()
        user_info['ip'] = input("IP User (enter untuk auto): ").strip()
        
        if not user_info['ip']:
            user_info['ip'] = get_local_ip()
        
        # Input konten PDF
        print("\n📄 MASUKKAN KONTEN PDF (ketik 'END' di baris baru untuk selesai):")
        lines = []
        while True:
            line = input()
            if line == 'END':
                break
            lines.append(line)
        
        content = '\n'.join(lines)
        
        # Generate PDF
        output_file = f"tracked_doc_{user_info['name']}.pdf"
        tracker.create_tracked_pdf(output_file, content, user_info)
        
    elif choice == '2':
        # Jalankan server
        server = PDFTrackerServer()
        try:
            server.run()
        except KeyboardInterrupt:
            print("\n🛑 Server dihentikan")
    
    elif choice == '3':
        # Lihat log
        if os.path.exists('tracking_log.txt'):
            with open('tracking_log.txt', 'r') as f:
                print("\n📋 TRACKING LOG:")
                print(f.read())
        else:
            print("❌ Belum ada log")
    
    elif choice == '4':
        print("👋 Sampai jumpa!")
        sys.exit(0)

if __name__ == "__main__":
    main()