# 1. Gunakan base image Python yang resmi dan ringan
FROM python:3.9-slim

# 2. Atur direktori kerja di dalam container
WORKDIR /app

# 3. Salin file requirements dan install semua library
# Ini dilakukan terpisah agar Docker bisa menggunakan cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Salin semua file proyek lainnya ke dalam container
COPY . .

# 5. Buat folder yang diperlukan untuk menyimpan data
RUN mkdir -p data analyses kamus templates

# 6. Set environment variables
ENV PYTHONUNBUFFERED=1

# 7. Expose port 5000
EXPOSE 5000

# 8. Jalankan aplikasi menggunakan Gunicorn saat container dimulai
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "300", "--workers", "2", "app:app"]
