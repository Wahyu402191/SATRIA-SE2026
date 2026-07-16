# SATRIA SE2026 - Testing Checklist

## Dashboard Structure Verification ✓

### 1. Landing & Selection Pages
- [✓] `templates/landing.html` - Dashboard awal aplikasi dengan desain SATRIA-SE2026
- [✓] `templates/selection.html` - Halaman pemilihan 3 dashboard aplikasi

### 2. YouTube Dashboard (Existing - No Changes)
- [✓] `/youtube/` - Beranda scraping & analisis YouTube
- [✓] `/youtube/analysis` - Halaman analisis sentimen
- [✓] `/youtube/comments` - Filter dan lihat komentar
- [✓] `/youtube/comparison` - Perbandingan 4 metode ML
- [✓] `/youtube/trend` - Trend kata per bulan
- [✓] `/youtube/about` - Tentang dashboard YouTube

### 3. Media Massa Dashboard (New)
- [✓] `/media/` - Beranda analisis Media Massa
- [✓] `/media/comments` - Filter dan lihat berita (Data Berita)
- [✓] `/media/comparison` - Perbandingan 4 metode ML
- [✓] `/media/trend` - Trend kata per minggu dalam 1 bulan
- [✓] `/media/about` - Tentang dashboard Media Massa

---

## Files Created/Modified

### Templates - Media Massa Dashboard
1. ✓ `templates_media_massa/base_media.html` - Base template dengan navbar
2. ✓ `templates_media_massa/index_media.html` - Halaman utama analisis
3. ✓ `templates_media_massa/comments_media.html` - Filter berita (positif/negatif/netral)
4. ✓ `templates_media_massa/comparison_media.html` - Perbandingan metode
5. ✓ `templates_media_massa/trend_media.html` - Trend kata per minggu
6. ✓ `templates_media_massa/about_media.html` - Info lengkap dashboard

### Python Modules
1. ✓ `media_massa_analyzer.py` - Analyzer untuk berita media massa
2. ✓ `media_massa_storage.py` - Storage layer untuk database media massa
3. ✓ `app.py` - Updated dengan routes untuk landing, selection, dan media massa

### Database
1. ✓ `database.sql` - Updated dengan 4 tabel media massa:
   - `news_sources` - Sumber media massa
   - `news_articles` - Artikel berita
   - `news_analysis_sessions` - Session analisis
   - `news_analysis_results` - Hasil analisis sentimen

---

## Routing Structure

```
/ (root)
├── Landing Page (SATRIA-SE2026 title)
│
├── /selection (Pilihan Dashboard)
│   ├── Button 1: Berita Sensus Ekonomi Terbaru
│   ├── Button 2: Analisis Sentiment Media Massa → /media/
│   └── Button 3: Scraping & Analisis Sentiment YouTube → /youtube/
│
├── /youtube/* (YouTube Dashboard - Existing)
│   ├── /youtube/ - Beranda
│   ├── /youtube/analysis - Analisis
│   ├── /youtube/comments - Komentar
│   ├── /youtube/comparison - Perbandingan
│   ├── /youtube/trend - Trend
│   └── /youtube/about - Tentang
│
└── /media/* (Media Massa Dashboard - New)
    ├── /media/ - Beranda/Analisis
    ├── /media/comments - Data Berita
    ├── /media/comparison - Perbandingan
    ├── /media/trend - Trend
    └── /media/about - Tentang
```

---

## Testing Instructions

### Prerequisites
1. MySQL Server running
2. Database `satria_se2026` created using `database.sql`
3. Python dependencies installed (`pip install -r requirements.txt`)
4. YouTube API Key configured in `.env` (untuk dashboard YouTube)

### Step-by-Step Testing

#### 1. Database Setup
```bash
# Import database schema
mysql -u root -p < database.sql

# Verify tables created
mysql -u root -p satria_se2026 -e "SHOW TABLES;"

# Expected output: 8 tables total
# - videos, comments, analysis_sessions, analysis_results (YouTube)
# - news_sources, news_articles, news_analysis_sessions, news_analysis_results (Media Massa)
```

#### 2. Start Application
```bash
python app.py
```

#### 3. Test Landing & Selection
- [ ] Navigate to `http://localhost:5000/`
- [ ] Verify landing page displays "SATRIA-SE2026"
- [ ] Click "Masuk Aplikasi" button
- [ ] Verify selection page shows 3 buttons
- [ ] Test each button navigates correctly

#### 4. Test YouTube Dashboard (Existing - Should Work)
- [ ] Click "Scraping & Analisis Sentiment YouTube"
- [ ] Verify all existing YouTube features work
- [ ] No changes to YouTube dashboard functionality

#### 5. Test Media Massa Dashboard
- [ ] From selection page, click "Analisis Sentiment Media Massa"
- [ ] Navigate to `/media/`
- [ ] Verify dashboard displays statistics (articles, months, sources, analyzed)
- [ ] Test month selection dropdown
- [ ] Test analyze button (requires data import first)

#### 6. Test Media Massa - Data Import (Manual)
**Note:** Data berita harus diimport manual oleh programmer menggunakan CSV/Excel

```python
# Example import script (run in Python console)
from media_massa_storage import MediaMassaStorage

storage = MediaMassaStorage()

# Import from CSV
storage.import_news_from_csv(
    'data_media_massa/januari_2026.csv',
    month=1,
    year=2026
)

# Or import from Excel
storage.import_news_from_excel(
    'data_media_massa/februari_2026.xlsx',
    month=2,
    year=2026
)
```

#### 7. Test Media Massa - Analysis Flow
After importing data:
- [ ] Select month from dropdown
- [ ] Select methods (default all 4 methods)
- [ ] Click "Analisis Sentimen"
- [ ] Verify analysis results display
- [ ] Check statistics show correctly
- [ ] Test wordcloud generation

#### 8. Test Media Massa - Comments/Data Berita
- [ ] Navigate to `/media/comments`
- [ ] Verify berita list displays
- [ ] Test filter chips (Semua, Positif, Negatif, Netral)
- [ ] Test search functionality
- [ ] Test sort functionality
- [ ] Click "Lihat Preprocessing" button
- [ ] Verify preprocessing modal shows 12 steps

#### 9. Test Media Massa - Comparison
- [ ] Navigate to `/media/comparison`
- [ ] Verify month badge shows selected month
- [ ] Verify per-method summary cards display
- [ ] Verify agreement rate section displays
- [ ] Verify distribution table displays

#### 10. Test Media Massa - Trend
- [ ] Navigate to `/media/trend`
- [ ] Verify month badge displays
- [ ] Verify top words chips display
- [ ] Verify line chart (trend per minggu) renders
- [ ] Verify bar chart (total per kata) renders
- [ ] Test chart interactivity

#### 11. Test Media Massa - About
- [ ] Navigate to `/media/about`
- [ ] Verify all sections display:
   - Hero section with description
   - 4 metode analisis sentimen
   - Pipeline preprocessing 12 langkah
   - Database structure
   - Features list
   - Data sources (CNN, Kompas, CNBC, Detik, Tempo, Republika)
   - Tech stack
   - Integration info

#### 12. Test Export Functionality
- [ ] Test Excel export (`/media/export`)
- [ ] Verify Excel file contains:
   - Ringkasan Metode sheet
   - Berita & Sentimen sheet
   - Agreement Rate sheet

#### 13. Test Navigation
- [ ] Test navbar navigation between pages
- [ ] Test "Kembali ke Beranda" button (returns to selection page)
- [ ] Verify consistent design across all pages
- [ ] Test responsive design (if applicable)

#### 14. Test Database Integration
- [ ] Verify data persists after app restart
- [ ] Verify statistics update correctly
- [ ] Check database foreign key constraints
- [ ] Verify analysis sessions are recorded

---

## Known Limitations & Notes

1. **Data Import**: Data berita media massa harus diimport manual oleh programmer menggunakan Python script atau CSV/Excel import function.

2. **Month Data**: Analisis hanya bisa dilakukan untuk bulan yang sudah memiliki data berita yang diimport.

3. **Trend Analysis**: Trend analysis membagi 1 bulan menjadi 4 minggu (bukan per hari).

4. **Design Consistency**: Dashboard Media Massa menggunakan design system yang sama dengan dashboard YouTube untuk konsistensi UI/UX.

5. **Database Requirement**: Aplikasi memerlukan MySQL server yang running untuk fungsi penuh. Jika MySQL tidak tersedia, akan menggunakan fallback mode dengan fitur terbatas.

---

## Success Criteria

✓ All pages load without errors
✓ All routes return correct templates
✓ Database tables created successfully
✓ Statistics display correctly
✓ Analysis functionality works
✓ Export functionality works
✓ Navigation between dashboards works
✓ Design consistency maintained
✓ No breaking changes to existing YouTube dashboard

---

## Troubleshooting

### Issue: "MySQL not connected"
**Solution:** Check MySQL server status, verify connection in `db_config.py`

### Issue: "No data available"
**Solution:** Import data berita using CSV/Excel import functions

### Issue: "Template not found"
**Solution:** Verify file paths and template names match routes in app.py

### Issue: Routes not working
**Solution:** Check app.py for correct route definitions, restart Flask server

---

## Final Notes

Aplikasi SATRIA SE2026 sekarang memiliki 3 dashboard:
1. **Dashboard Awal** - Landing page dengan branding
2. **Dashboard YouTube** - Scraping & analisis sentiment komentar YouTube
3. **Dashboard Media Massa** - Analisis sentiment berita dari media massa

Semua dashboard terintegrasi dengan baik dan menggunakan:
- 4 metode ML yang sama (Naive Bayes, SVM, LSTM, IndoBERT)
- Pipeline preprocessing yang identik (12 langkah)
- Database leksikon yang sama
- Design system yang konsisten

**Status: READY FOR TESTING** ✓
