# 🚀 Akıllı Müşteri Segmentasyonu — RFM & Fuzzy C-Means Dashboard

> Müşteri davranışlarını RFM veya PRM modeliyle, Fuzzy C-Means algoritması ve üyelik tabanlı öneri skorlarıyla segmentlere ayıran interaktif veri bilimi uygulaması.

---

## 📌 Proje Hakkında

Bu uygulama, e-ticaret ve dijital ürün ekiplerinin müşteri verilerini analiz etmesine olanak tanır. Veri yapısına göre tek model çalışır: **RFM (Recency, Frequency, Monetary)** veya **PRM (Preference, Response, Monetary)**. İki model aynı analizde karıştırılmaz.

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
| 🤖 Optimal K Seçimi | K=2..6 aralığında FPC + PE + XB hibrit skoru ile en iyi küme sayısı |
| 🧮 Dinamik Skorlama | Centroid sıralaması ve üyelik matrisi ile RFM_Score/PRM_Score + Final_Score |
| 🎯 3D Görselleştirme | Interaktif 3D küme dağılım grafiği |
| 📈 RFM Dağılımları | 2D scatter ve donut grafikleri |
| 💡 İş Önerileri | Her kullanıcı için ana öneri etiketi ve 3-4 maddelik aksiyon listesi |
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

Uygulama RFM veya PRM yapısını otomatik algılar.

### RFM Veri Formatı

| Sütun | Açıklama | Örnek |
|---|---|---|
| `Customer ID` | Benzersiz müşteri kimliği | `12345` |
| `InvoiceDate` | İşlem tarihi | `2023-01-15` |
| `Quantity` | Satın alınan ürün miktarı | `3` |
| `Price` | Birim fiyat | `29.99` |

### PRM Veri Formatı

| Sütun | Açıklama | Örnek |
|---|---|---|
| `Customer_ID` | Benzersiz kullanıcı/müşteri kimliği | `12345` |
| `Product_Category` | Kullanıcının etkileştiği ürün kategorisi | `Electronics` |
| `Session_Duration_Minutes` | Ortalama veya kayıt bazlı oturum süresi | `8.5` |
| `Pages_Viewed` | Gezilen sayfa sayısı | `6` |
| `Total_Amount` | İşlem veya sepet tutarı | `249.90` |

> **Not:** Sütun adları farklıysa endişelenmeyin — uygulama içindeki **Gelişmiş Ayarlar** panelinden sütun eşleştirmesi yapabilirsiniz.

---

## 🖥️ Kullanım

1. Sol panelden **CSV dosyanızı yükleyin**
2. Gerekirse **Gelişmiş Ayarlar**'dan sütunları eşleştirin
3. **Optimal K'yı Otomatik Bul** seçeneğini açık bırakın (önerilir) ya da manuel K=2..6 arasında seçim yapın
4. **🚀 Analizi Başlat** butonuna tıklayın
5. Sonuçları sekmelerde inceleyin:
   - **3D Segmentasyon Grafiği** — Kümelerin uzaysal dağılımı
   - **RFM Dağılımları** — 2D scatter ve pasta grafikleri
   - **İşletme Önerileri** — Segment aksiyonları ve kullanıcı bazlı öneri çıktısı
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

### PRM Dönüşümü

PRM verisi müşteri bazında gruplanır. `Product_Category` için mod alınır, `Session_Duration_Minutes` ve `Pages_Viewed` ortalanır, `Total_Amount` toplanır. Oturum ve sayfa metrikleri MinMax ile normalize edilerek tek `Response` skoru oluşturulur:

```
Response = (Session_Norm + Pages_Norm) / 2
```

Modelde kullanılan PRM alanları `Response` ve `Monetary` değerleridir.

### Üyelik Tabanlı Öneri Skoru

Her K için küme centroid değerleri dinamik olarak sıralanır ve skorlar `(rank / K) * 5` formülüyle üretilir. Müşteri final skoru, üyelik değerleri ile küme skorlarının ağırlıklı ortalamasıdır:

```
FinalScore = Σ (μ_i * Score_i)
```

RFM modeli çalışıyorsa `RFM_Score`, PRM modeli çalışıyorsa `PRM_Score` üretilir. Çıktı dosyasında müşteri kimliği, üyelik değerleri, model skoru, final skor, segment etiketi ve öneri listesi yer alır.

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
