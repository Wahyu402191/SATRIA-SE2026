"""
Import dataset dummy besar berita Sensus Ekonomi 2026 (Januari-Juni) ke database.
Menghapus data dummy lama (36 artikel + hasil analisis lamanya) lalu mengganti
dengan dataset baru yang lebih besar (~1.200 artikel) dari data_media_massa/SATRIA_SE2026_berita_dummy_besar.xlsx
"""
from media_massa_storage import MediaMassaStorage
from db_config import execute_query

MONTHS = [
    (1, 'Januari'),
    (2, 'Februari'),
    (3, 'Maret'),
    (4, 'April'),
    (5, 'Mei'),
    (6, 'Juni'),
]

def clear_old_dummy_data():
    print("[i] Menghapus data dummy lama (news_articles cascades ke news_analysis_results)...")
    execute_query("DELETE FROM news_articles")
    execute_query("DELETE FROM news_analysis_sessions")
    print("[i] Data lama sudah dibersihkan.")

def main():
    storage = MediaMassaStorage()
    if not storage.use_mysql:
        print("[X] Tidak bisa import: MySQL tidak terhubung atau tabel belum dibuat.")
        return

    clear_old_dummy_data()

    xlsx_path = 'data_media_massa/SATRIA_SE2026_berita_dummy_besar.xlsx'
    total = 0
    for month_num, sheet_name in MONTHS:
        count = storage.import_news_from_excel(
            xlsx_path, month=month_num, year=2026, sheet_name=sheet_name
        )
        total += count
        print(f"    {sheet_name}: {count} artikel")
    print(f"\n[DONE] Total {total} artikel berhasil diimport ke database.")

if __name__ == '__main__':
    main()
