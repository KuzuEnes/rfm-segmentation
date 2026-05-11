import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score


# =============================================================================
# Fuzzy C-Means — pure NumPy implementation (skfuzzy yerine)
# skfuzzy kütüphanesi Python 3.14 ile uyumsuz olduğu için kaldırıldı.
# =============================================================================

def _fuzzy_cmeans(data, c, m=2, error=0.005, maxiter=1000):
    """
    Basit Fuzzy C-Means algoritması (saf NumPy).
    data : (n_features, n_samples) — skfuzzy ile aynı format
    c    : küme sayısı
    m    : bulanıklık katsayısı (genellikle 2)
    Döner: cntr (c, n_features), u (c, n_samples), fpc (float)
    """
    n_features, n_samples = data.shape
    rng = np.random.default_rng(42)

    # Rastgele üyelik matrisi başlat ve normalize et
    u = rng.dirichlet(np.ones(c), size=n_samples).T  # (c, n_samples)

    for _ in range(maxiter):
        u_old = u.copy()

        # Küme merkezleri: (c, n_features)
        um = u ** m
        cntr = (um @ data.T) / um.sum(axis=1, keepdims=True)  # (c, n_features)

        # Mesafeler: (c, n_samples)
        dist = np.zeros((c, n_samples))
        for i in range(c):
            diff = data.T - cntr[i]          # (n_samples, n_features)
            dist[i] = np.sqrt((diff ** 2).sum(axis=1)) + 1e-10

        # Üyelik güncelle
        exp = 2.0 / (m - 1)
        u_new = np.zeros((c, n_samples))
        for i in range(c):
            ratio = (dist[i][np.newaxis, :] / dist)  # (c, n_samples)
            u_new[i] = 1.0 / (ratio ** exp).sum(axis=0)

        u = u_new

        # Yakınsama kontrolü
        if np.max(np.abs(u - u_old)) < error:
            break

    # FPC (Fuzzy Partition Coefficient)
    fpc = float(np.sum(u ** 2) / n_samples)

    # Mesafeleri son durumda hesapla (run_fuzzy_cmeans'e lazım)
    dist_final = np.zeros((c, n_samples))
    for i in range(c):
        diff = data.T - cntr[i]
        dist_final[i] = np.sqrt((diff ** 2).sum(axis=1)) + 1e-10

    return cntr, u, dist_final, fpc


# =============================================================================
# Genel API fonksiyonları
# =============================================================================

RFM_COLUMN_ALIASES = {
    'customer_id_col': ['Customer ID', 'CustomerID', 'Customer_ID', 'customer_id'],
    'invoice_date_col': ['InvoiceDate', 'Invoice Date', 'Date', 'OrderDate', 'Order_Date'],
    'quantity_col': ['Quantity', 'Qty', 'quantity'],
    'price_col': ['Price', 'UnitPrice', 'Unit_Price', 'Unit Price'],
    'amount_col': ['TotalPrice', 'Total Price', 'Total_Amount', 'Total Amount', 'Amount'],
    'order_id_col': ['InvoiceNo', 'Invoice ID', 'Order_ID', 'Order ID', 'order_id'],
}

PRM_REQUIRED_COLUMNS = {
    'Customer_ID',
    'Product_Category',
    'Customer_Rating',
    'Session_Duration_Minutes',
    'Pages_Viewed',
    'Total_Amount',
}

RFM_FEATURE_COLUMNS = ['Recency', 'Frequency', 'Monetary']
PRM_FEATURE_COLUMNS = [
    'Average_Rating',
    'Average_Session_Duration',
    'Average_Pages_Viewed',
    'Monetary',
]


def _normalize_col_name(col):
    return str(col).strip().lower().replace(' ', '').replace('_', '')


def _find_column(cols, aliases):
    normalized = {_normalize_col_name(col): col for col in cols}
    for alias in aliases:
        match = normalized.get(_normalize_col_name(alias))
        if match is not None:
            return match
    return None


def detect_dataset_structure(df):
    """
    Sütun adlarına göre veri setinin RFM mi PRM mi olduğunu ve varsayılan
    eşleştirmeleri belirler.
    """
    cols = df.columns.tolist()
    normalized_cols = {_normalize_col_name(col) for col in cols}
    prm_score = sum(_normalize_col_name(col) in normalized_cols for col in PRM_REQUIRED_COLUMNS)

    mapping = {
        key: _find_column(cols, aliases)
        for key, aliases in RFM_COLUMN_ALIASES.items()
    }

    has_prm_core = prm_score == len(PRM_REQUIRED_COLUMNS)
    has_rfm_core = all(mapping[key] for key in [
        'customer_id_col',
        'invoice_date_col',
        'quantity_col',
    ]) and (mapping['price_col'] or mapping['amount_col'])

    dataset_type = 'PRM' if has_prm_core else 'RFM'
    if not has_prm_core and not has_rfm_core:
        dataset_type = 'Bilinmeyen'

    return {
        'type': dataset_type,
        'mapping': mapping,
        'prm_score': prm_score,
    }


def process_data(df, customer_id_col='Customer ID', invoice_date_col='InvoiceDate',
                 quantity_col='Quantity', price_col='Price', amount_col=None,
                 order_id_col=None):
    """
    Veriyi temizler ve segmentasyon için Recency/Frequency/Monetary tablosunu oluşturur.
    """
    df = df[df[customer_id_col].notna()].copy()
    df[invoice_date_col] = pd.to_datetime(df[invoice_date_col])

    if amount_col is None:
        detected = detect_dataset_structure(df)['mapping']
        amount_col = detected.get('amount_col')

    if amount_col and amount_col in df.columns:
        df['TotalPrice'] = pd.to_numeric(df[amount_col], errors='coerce')
    elif 'TotalPrice' not in df.columns:
        df['TotalPrice'] = (
            pd.to_numeric(df[quantity_col], errors='coerce') *
            pd.to_numeric(df[price_col], errors='coerce')
        )

    df['CustomerID'] = df[customer_id_col].astype(str)
    df = df[df['TotalPrice'].notna()].copy()

    analysis_date = df[invoice_date_col].max() + pd.Timedelta(days=1)
    frequency_source = order_id_col if order_id_col in df.columns else invoice_date_col
    frequency_agg = 'nunique' if frequency_source == order_id_col else 'count'

    rfm = df.groupby('CustomerID').agg(
        Recency=(invoice_date_col, lambda x: (analysis_date - x.max()).days),
        Frequency=(frequency_source, frequency_agg),
        Monetary=('TotalPrice', 'sum')
    ).reset_index()

    return rfm


def process_prm_data(df):
    """
    PRM feature engineering:
    Preference: Preferred_Category, Average_Rating
    Response: Average_Session_Duration, Average_Pages_Viewed
    Monetary: Monetary
    """
    work_df = df.copy()
    required = list(PRM_REQUIRED_COLUMNS)
    missing = [col for col in required if col not in work_df.columns]
    if missing:
        raise ValueError(f"PRM analizi için eksik sütunlar: {', '.join(missing)}")

    for col in ['Customer_Rating', 'Session_Duration_Minutes', 'Pages_Viewed', 'Total_Amount']:
        work_df[col] = pd.to_numeric(work_df[col], errors='coerce')

    work_df = work_df.dropna(subset=[
        'Customer_ID',
        'Product_Category',
        'Customer_Rating',
        'Session_Duration_Minutes',
        'Pages_Viewed',
        'Total_Amount',
    ])

    prm = work_df.groupby('Customer_ID').agg({
        'Product_Category': lambda x: x.mode().iloc[0],
        'Customer_Rating': 'mean',
        'Session_Duration_Minutes': 'mean',
        'Pages_Viewed': 'mean',
        'Total_Amount': 'sum',
    }).reset_index()

    prm.columns = [
        'CustomerID',
        'Preferred_Category',
        'Average_Rating',
        'Average_Session_Duration',
        'Average_Pages_Viewed',
        'Monetary',
    ]

    return prm


def get_feature_columns(dataset_type):
    return PRM_FEATURE_COLUMNS if dataset_type == 'PRM' else RFM_FEATURE_COLUMNS


def _make_cluster_names_unique(recommendations):
    seen = {}
    for cluster_id, details in recommendations.items():
        name = details['name']
        if name not in seen:
            seen[name] = 1
            continue

        seen[name] += 1
        metrics = details.get('metrics', {})
        if metrics:
            dominant_metric = max(metrics, key=lambda key: abs(float(metrics[key])))
            suffix = f"{dominant_metric.replace('_', ' ')} Profili {seen[name]}"
        else:
            suffix = f"Varyant {seen[name]}"
        details['name'] = f"{name} - {suffix}"


def find_optimal_k(data_transposed, k_min=2, k_max=8):
    """
    Fuzzy C-Means için optimal K sayısını bulur (hibrit FPC + PE + XB skoru).
    """
    best_k = 3
    best_hybrid_score = -1

    for k in range(k_min, k_max + 1):
        cntr, u, d, fpc = _fuzzy_cmeans(data_transposed, c=k, m=2, error=0.005, maxiter=500)

        # Partition Entropy (PE)
        u_log = np.where(u > 0, u * np.log(u), 0)
        pe = -np.sum(u_log) / u.shape[1]

        # Xie-Beni Index (XB)
        n_samples = u.shape[1]
        compactness = np.sum((u ** 2) * (d ** 2))
        min_center_dist = np.inf
        for i in range(k):
            for j in range(i + 1, k):
                dist_ij = np.sum((cntr[i] - cntr[j]) ** 2)
                if dist_ij < min_center_dist:
                    min_center_dist = dist_ij
        xb = compactness / (n_samples * min_center_dist) if min_center_dist > 0 else np.inf

        # Hibrit skor
        pe_norm = max(0, min(1, 1 - pe / 2))
        xb_norm = max(0, min(1, 1 - xb / 2))
        hybrid_score = (fpc + pe_norm + xb_norm) / 3

        if hybrid_score > best_hybrid_score:
            best_hybrid_score = hybrid_score
            best_k = k

    return best_k


def run_fuzzy_cmeans(data, n_clusters, feature_cols=None):
    """
    Belirli bir K değeri için Fuzzy C-Means çalıştırır ve sonuçları döner.
    """
    if feature_cols is None:
        feature_cols = RFM_FEATURE_COLUMNS

    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data[feature_cols])
    data_transposed = data_scaled.T  # (n_features, n_samples)

    cntr, u, d, fpc = _fuzzy_cmeans(data_transposed, c=n_clusters, m=2, error=0.005, maxiter=1000)

    cluster_labels = np.argmax(u, axis=0)
    results = data.copy()
    results['Cluster'] = cluster_labels

    for i in range(n_clusters):
        results[f'Membership_C{i}'] = u[i]

    # Küme merkezlerini orijinal ölçeğe çevir
    cluster_centers = scaler.inverse_transform(cntr)
    centers_df = pd.DataFrame(cluster_centers, columns=feature_cols)
    centers_df['Cluster'] = range(n_clusters)

    try:
        silhouette_avg = silhouette_score(data_scaled, cluster_labels)
    except Exception:
        silhouette_avg = 0.0

    return results, centers_df, silhouette_avg, fpc


def get_cluster_recommendations(results_with_clusters, centers_df, dataset_type='RFM'):
    """
    Kümelerin özelliklerine göre iş önerileri üretir.
    """
    recommendations = {}
    monetary_median = centers_df['Monetary'].median()
    rating_median = centers_df['Average_Rating'].median() if 'Average_Rating' in centers_df.columns else None
    session_median = centers_df['Average_Session_Duration'].median() if 'Average_Session_Duration' in centers_df.columns else None
    pages_median = centers_df['Average_Pages_Viewed'].median() if 'Average_Pages_Viewed' in centers_df.columns else None

    for idx, row in centers_df.iterrows():
        cluster_id = int(row['Cluster'])
        count = len(results_with_clusters[results_with_clusters['Cluster'].astype(int) == cluster_id])

        if dataset_type == 'PRM':
            rating = row['Average_Rating']
            session = row['Average_Session_Duration']
            pages = row['Average_Pages_Viewed']
            monetary = row['Monetary']

            high_rating = rating >= rating_median
            high_engagement = session >= session_median or pages >= pages_median
            high_monetary = monetary >= monetary_median
            page_dominant = pages >= pages_median and session < session_median
            session_dominant = session >= session_median and pages < pages_median

            if high_rating and high_engagement and high_monetary:
                name = "🌟 Bağlı ve Yüksek Değerli Müşteriler"
                description = "Memnuniyet, etkileşim ve harcama seviyesi birlikte yüksek olan en güçlü PRM grubudur."
                recs = [
                    "Kişiselleştirilmiş ürün önerileri sunulmalı",
                    "Favori kategori bazlı kampanyalar hazırlanmalı",
                    "Premium sadakat teklifleri uygulanmalı",
                ]
                cautions = [
                    "Aşırı kampanya sıklığı memnun müşterilerde yorgunluk yaratabilir",
                    "Öneriler müşterinin tercih ettiği kategoriyle uyumlu tutulmalı",
                ]
            elif high_rating and high_engagement and not high_monetary:
                name = "🎯 Etkileşimli Potansiyel Müşteriler"
                description = "Memnun ve aktif gezinen, fakat parasal değeri henüz yüksek seviyeye çıkmamış müşterilerdir."
                recs = [
                    "Cross-sell ve up-sell teklifleri gösterilmeli",
                    "Sepet tutarını artıracak paket önerileri sunulmalı",
                    "Memnun oldukları kategorilerde tamamlayıcı ürünler öne çıkarılmalı",
                ]
                cautions = [
                    "Fiyat hassasiyeti yüksek olabilir; agresif premium tekliflerden kaçınılmalı",
                    "Dönüşüm oranı düzenli izlenmeli",
                ]
            elif high_rating and not high_engagement and high_monetary:
                name = "💎 Memnun ve Hızlı Alışverişçiler"
                description = "Memnuniyet ve harcama seviyesi yüksek, ancak gezinme/oturum davranışı daha kısa olan müşterilerdir."
                recs = [
                    "Satın alma yolunu kısaltan hızlı tekrar alışveriş seçenekleri sunulmalı",
                    "Önceki tercihleri temel alan doğrudan ürün önerileri gösterilmeli",
                    "Favori kategori hatırlatmaları kullanılmalı",
                ]
                cautions = [
                    "Bu müşteriler uzun içeriklerle yorulmamalı",
                    "Hızlı satın alma deneyimindeki sürtünmeler düzenli kontrol edilmeli",
                ]
            elif high_rating and not high_engagement and not high_monetary:
                name = "🙂 Memnun fakat Düşük Bağlılıkta Müşteriler"
                description = "Memnuniyet olumlu olsa da etkileşim ve harcama seviyesi sınırlı kalan müşterilerdir."
                recs = [
                    "Düşük bariyerli tekrar alışveriş teklifleri sunulmalı",
                    "İlgi kategorilerine göre kısa ve net kampanya mesajları hazırlanmalı",
                    "Küçük sepetleri büyütecek tamamlayıcı ürünler önerilmeli",
                ]
                cautions = [
                    "Memnuniyet tek başına yüksek gelir potansiyeli anlamına gelmez",
                    "Kampanya maliyeti müşteri değerine göre sınırlanmalı",
                ]
            elif not high_rating and high_engagement and high_monetary:
                name = "⚠️ Değerli ama Kararsız Müşteriler"
                description = "Harcama ve etkileşim yüksek, fakat memnuniyet görece düşük olduğu için kayıp riski taşıyan gruptur."
                recs = [
                    "Memnuniyetsizlik nedenleri ürün veya deneyim bazında incelenmeli",
                    "Destek, iade ve teslimat deneyimi iyileştirilmeli",
                    "Yüksek değerli müşterilere özel telafi teklifleri sunulmalı",
                ]
                cautions = [
                    "Sadece indirim vermek temel memnuniyet problemini çözmeyebilir",
                    "Negatif deneyim tekrar ederse yüksek değerli müşteri kaybı oluşabilir",
                ]
            elif not high_rating and high_engagement and not high_monetary:
                name = "👀 Araştırma Aşamasındaki Müşteriler"
                if page_dominant:
                    name = "👀 Çok Gezen Araştırmacı Müşteriler"
                elif session_dominant:
                    name = "⏱️ Uzun Oturumlu Kararsız Müşteriler"
                description = "Etkileşimi yüksek ancak memnuniyet veya harcama seviyesi sınırlı olan, karar verme süreci uzayan müşterilerdir."
                recs = [
                    "Kararsızlığı azaltan ürün karşılaştırmaları gösterilmeli",
                    "İncelediği kategoriye özel hatırlatma kampanyası yapılmalı",
                    "Yorumlar, puanlar ve stok bilgisi görünür hale getirilmeli",
                ]
                cautions = [
                    "Uzun oturum her zaman satın alma niyeti anlamına gelmez",
                    "Navigasyon veya ürün bulma problemleri ayrıca kontrol edilmeli",
                ]
            elif not high_rating and not high_engagement and high_monetary:
                name = "💰 Sessiz Yüksek Harcayanlar"
                description = "Etkileşim ve memnuniyet sinyali düşük olsa da parasal katkısı yüksek olan müşterilerdir."
                recs = [
                    "Satın alma sonrası memnuniyet anketleriyle risk nedenleri ölçülmeli",
                    "Yüksek harcama kategorilerine özel servis kalitesi artırılmalı",
                    "Basit ve doğrudan tekrar satın alma teklifleri sunulmalı",
                ]
                cautions = [
                    "Düşük memnuniyet sinyali kayıp riskini artırabilir",
                    "Bu grupta deneyim problemleri parasal kayba dönüşebilir",
                ]
            else:
                name = "📉 Düşük Etkileşimli Müşteriler"
                description = "Düşük memnuniyet, kısa oturum veya sınırlı gezinme davranışı gösteren düşük bağlılık grubudur."
                recs = [
                    "Basit ve düşük maliyetli yeniden etkileşim kampanyaları uygulanmalı",
                    "Daha net kategori önerileri ve kısa kampanya mesajları kullanılmalı",
                    "İlk dönüşümü kolaylaştıracak küçük teşvikler denenmeli",
                ]
                cautions = [
                    "Yüksek pazarlama maliyeti bu grupta geri dönüş sağlamayabilir",
                    "Düşük etkileşimin veri eksikliğinden kaynaklanmadığı kontrol edilmeli",
                ]

            recommendations[cluster_id] = {
                'name': name,
                'description': description,
                'recommendations': recs,
                'cautions': cautions,
                'rec': '\n\n'.join(f"• {item}" for item in recs),
                'count': count,
                'metrics': {
                    'Average_Rating': rating,
                    'Average_Session_Duration': session,
                    'Average_Pages_Viewed': pages,
                    'Monetary': monetary,
                },
            }
            continue

        r = row['Recency']
        f = row['Frequency']
        m = row['Monetary']

        if r < 100 and f > 50:
            name = "🌟 Sadık Müşteriler (Champions / Loyal Customers)"
            description = "Yakın zamanda alışveriş yapan, sık işlem gerçekleştiren ve markayla güçlü ilişkisi olan müşteriler."
            recs = [
                "VIP müşteri programı oluşturulmalı",
                "Özel indirim kuponları sunulmalı",
                "Sadakat programı uygulanmalı",
                "Premium ürün önerileri yapılmalı",
            ]
            cautions = [
                "Gereksiz indirimlerle marj düşürülmemeli",
                "Bu müşterilerin memnuniyet ve tekrar alışveriş trendi yakından izlenmeli",
            ]
        elif r < 100 and f <= 20:
            name = "👋 Yeni Müşteriler"
            description = "Yakın zamanda işlem yapan ancak alışveriş sıklığı henüz düşük olan yeni veya erken dönem müşteriler."
            recs = [
                "Hoş geldin kampanyası uygulanmalı",
                "İkinci alışverişi tetikleyecek teklif sunulmalı",
                "Marka güveni artırılmalı",
            ]
            cautions = [
                "Bu grubun sadık müşteri olduğu varsayılmamalı",
                "İlk deneyim sonrası geri dönüş süresi takip edilmeli",
            ]
        elif r < 100 and 20 < f <= 50:
            name = "🎯 Potansiyel Sadık Müşteriler"
            description = "Güncel ve tekrar eden satın alma davranışı gösteren, sadakat potansiyeli yüksek müşteriler."
            recs = [
                "Cross-sell ve up-sell stratejileri uygulanmalı",
                "Paket kampanyaları sunulmalı",
                "Sadakat programına dahil edilmeli",
            ]
            cautions = [
                "Teklifler müşterinin alışveriş geçmişiyle uyumlu olmalı",
                "Fazla geniş kampanyalar segmentin gerçek potansiyelini maskeleyebilir",
            ]
        elif 100 <= r < 250 and f > 20:
            name = "⚠️ Kaybedilme Riski Olanlar (At Risk)"
            description = "Geçmişte sık alışveriş yapan ancak son dönemde uzaklaşma sinyali veren müşteriler."
            recs = [
                "Geri kazanım kampanyası uygulanmalı",
                "Kişiselleştirilmiş e-posta gönderilmeli",
                "Özel geri dönüş indirimleri sunulmalı",
                "SMS ile hatırlatma yapılmalı",
            ]
            cautions = [
                "Teklif zamanlaması doğru yapılmalı; çok geç aksiyon kaybı artırabilir",
                "İndirim bağımlılığı yaratmamak için kampanya sınırlandırılmalı",
            ]
        elif 100 <= r < 300 and f <= 20:
            name = "💤 Uyuyan Müşteriler"
            description = "Alışveriş sıklığı ve güncelliği düşük, yeniden aktive edilmesi gereken müşteriler."
            recs = [
                "Re-activation kampanyası yapılmalı",
                "Son şans teklifleri sunulmalı",
                "Düşük maliyetli hatırlatma iletişimi kullanılmalı",
            ]
            cautions = [
                "Bu gruba yüksek bütçeli kampanya ayırmadan önce dönüş potansiyeli test edilmeli",
                "İletişim izinleri ve pasiflik süresi kontrol edilmeli",
            ]
        else:
            name = "📉 Düşük Değerli Müşteriler"
            description = "Güncellik, sıklık veya parasal değer açısından düşük katkı sağlayan müşteri grubu."
            recs = [
                "Düşük maliyetli kampanyalar uygulanmalı",
                "Otomatik pazarlama tercih edilmeli",
                "Genel kampanyalarla düşük eforlu iletişim kurulmalı",
            ]
            cautions = [
                "Bu segment için müşteri edinme ve pazarlama maliyeti dikkatle sınırlandırılmalı",
                "Veri kalitesi veya eksik işlem geçmişi yanlış sınıflandırmaya neden olabilir",
            ]

        recommendations[cluster_id] = {
            'name': name,
            'description': description,
            'recommendations': recs,
            'cautions': cautions,
            'rec': '\n\n'.join(f"• {item}" for item in recs),
            'count': count,
            'metrics': {
                'Recency': r,
                'Frequency': f,
                'Monetary': m,
            },
            'avg_r': r,
            'avg_f': f,
            'avg_m': m,
        }

    _make_cluster_names_unique(recommendations)
    return recommendations
