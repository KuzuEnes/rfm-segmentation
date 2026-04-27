# 🚀 Akıllı Müşteri Segmentasyonu — RFM & Fuzzy C-Means Dashboard

> Müşteri davranışlarını RFM analizi ve Bulanık K-Means (Fuzzy C-Means) algoritması ile segmentlere ayıran, interaktif bir veri bilimi uygulaması.

---

## 📌 Proje Hakkında

Bu uygulama, e-ticaret ve perakende işletmelerinin müşteri verilerini analiz etmesine olanak tanır. **RFM (Recency, Frequency, Monetary)** metriklerini kullanarak her müşterinin davranışsal profilini çıkarır ve **Fuzzy C-Means** algoritması ile müşterileri anlamlı segmentlere ayırır.

Her segment için otomatik olarak iş önerileri üretilir: sadakat programları, geri kazanım kampanyaları, VIP programları ve daha fazlası.

### Neden Fuzzy C-Means?

Klasik K-Means algoritmalarında her müşteri yalnızca tek bir kümeye atanır. Fuzzy C-Means ise her müşteriye tüm kümeler için bir **üyelik derecesi** atar. Bu sayede:
- Sınır durumdaki müşteriler daha doğru temsil edilir
- Segmentler arası geçiş dönemindeki müşteriler yakalanır
- Model çok daha esnek ve gerçekçi sonuçlar üretir

---

## 🎯 Özellikler

| Özellik | Açıklama |
|---|---|
| 📂 CSV Yükleme | Sütun eşleştirme ile herhangi bir e-ticaret verisi |
| 📊 RFM Analizi | Recency, Frequency, Monetary otomatik hesaplama |
| 🤖 Optimal K Seçimi | FPC + PE + XB hibrit skoru ile en iyi küme sayısı |
| 🎯 3D Görselleştirme | Interaktif 3D küme dağılım grafiği |
| 📈 RFM Dağılımları | 2D scatter ve donut grafikleri |
| 💡 İş Önerileri | Segment bazlı otomatik aksiyon planı |
| 🔎 Müşteri Profili | Bireysel müşteri sorgulama ve son işlem geçmişi |
| ⬇️ CSV İndirme | Segmentasyon sonuçlarını dışa aktarma |

---

## 🛠️ Teknolojiler

- **Python 3.14**
- **Streamlit** — Web arayüzü
- **Pandas / NumPy** — Veri işleme
- **Scikit-learn** — Normalizasyon ve Silhouette skoru
- **Plotly** — İnteraktif grafikler
- **Fuzzy C-Means** — Saf NumPy implementasyonu (dış bağımlılık yok)

---

## 📦 Kurulum

### 1. Repoyu klonlayın
```bash
git clone https://github.com/KuzuEnes/rfm-segmentation.git
cd rfm-segmentation
```

### 2. Sanal ortam oluşturun ve aktif edin
```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### 3. Gerekli kütüphaneleri yükleyin
```bash
pip install -r requirements.txt
```

### 4. Uygulamayı başlatın
```bash
streamlit run app.py
```

Tarayıcınızda otomatik olarak `http://localhost:8501` açılacaktır.

---

## 📋 Veri Formatı

Uygulama, aşağıdaki sütun yapısına sahip bir CSV dosyası bekler:

| Sütun | Açıklama | Örnek |
|---|---|---|
| `Customer ID` | Benzersiz müşteri kimliği | `12345` |
| `InvoiceDate` | İşlem tarihi | `2023-01-15` |
| `Quantity` | Satın alınan ürün miktarı | `3` |
| `Price` | Birim fiyat | `29.99` |

> **Not:** Sütun adları farklıysa endişelenmeyin — uygulama içindeki **Gelişmiş Ayarlar** panelinden sütun eşleştirmesi yapabilirsiniz.

---

## 🖥️ Kullanım

1. Sol panelden **CSV dosyanızı yükleyin**
2. Gerekirse **Gelişmiş Ayarlar**'dan sütunları eşleştirin
3. **Optimal K'yı Otomatik Bul** seçeneğini açık bırakın (önerilir) ya da manuel K girin
4. **🚀 Analizi Başlat** butonuna tıklayın
5. Sonuçları sekmelerde inceleyin:
   - **3D Segmentasyon Grafiği** — Kümelerin uzaysal dağılımı
   - **RFM Dağılımları** — 2D scatter ve pasta grafikleri
   - **İşletme Önerileri** — Her segment için aksiyon planı
   - **Müşteri Sorgulama** — Bireysel müşteri profili
6. **Sonuçları CSV Olarak İndir** ile dışa aktarın

---

## 📁 Proje Yapısı

```
rfm-segmentation/
│
├── app.py              # Ana Streamlit uygulaması (arayüz + iş mantığı)
├── segmentation.py     # Fuzzy C-Means algoritması ve RFM hesaplama
├── requirements.txt    # Python bağımlılıkları
│
├── .streamlit/
│   └── config.toml     # Streamlit tema ayarları (Dark Professional)
│
└── .gitignore
```

---

## 🧮 Algoritma Detayı

### RFM Metrikleri
- **Recency (R):** Müşterinin son alışverişinden bu yana geçen gün sayısı
- **Frequency (F):** Toplam işlem sayısı
- **Monetary (M):** Toplam harcama tutarı

### Optimal K Seçimi (Hibrit Skor)
Optimal küme sayısı üç metriğin ortalaması ile belirlenir:

```
Hibrit Skor = (FPC + PE_normalized + XB_normalized) / 3
```

- **FPC** (Fuzzy Partition Coefficient): Küme ayrışımının netliği
- **PE** (Partition Entropy): Belirsizlik ölçümü
- **XB** (Xie-Beni Index): Kompaktlık / ayrışım oranı

---

## 📸 Ekran Görüntüleri

> Uygulamayı çalıştırarak Dark Professional temasıyla analiz sonuçlarını görebilirsiniz.

---

## 👤 Geliştirici

**KuzuEnes**
- GitHub: [@KuzuEnes](https://github.com/KuzuEnes)

---

## 📄 Lisans

Bu proje akademik amaçlı geliştirilmiştir.
