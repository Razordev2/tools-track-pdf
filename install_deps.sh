#!/bin/bash
echo "📦 Menginstall dependencies untuk PDF Tracker..."

# Install pip3 jika belum ada
sudo apt update
sudo apt install python3-pip -y

# Install semua library
pip3 install --user requests reportlab fpdf PyPDF2 pillow qrcode[pil] cryptography flask

echo "✅ Selesai! Jalankan dengan: python3 pdf_tracker.py"