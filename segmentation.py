import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler
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

PRM_COLUMN_ALIASES = {
    'customer_id_col': ['Customer_ID', 'Customer ID', 'CustomerID', 'customer_id'],
    'session_col': ['Session_Duration_Minutes', 'Session Duration', 'SessionDuration', 'Oturum_Suresi'],
    'pages_col': ['Pages_Viewed', 'Pages Viewed', 'PagesViewed', 'Gezilen_Sayfa'],
    'rating_col': ['Customer_Rating', 'Customer Rating', 'Rating', 'Puan'],
    'category_col': ['Product_Category', 'Category', 'Preferred_Category', 'Kategori'],
    'amount_col': ['Total_Amount', 'Total Amount', 'Amount', 'Monetary', 'Harcama'],
}

RFM_FEATURE_COLUMNS = ['Recency', 'Frequency', 'Monetary']
PRM_FEATURE_COLUMNS = ['preference_score', 'engagement_score', 'monetary_score']

RFM_SEGMENT_DEFINITIONS = [
    (0.0, 1.5, "Geri kazanım (reaktivasyon)", [
        "Son alışverişten uzaklaşan müşteriye düşük bariyerli geri dönüş teklifi gönder.",
        "Önceki alışveriş kategorisine göre hatırlatma ve yeniden aktivasyon mesajı hazırla.",
        "Kampanya maliyetini sınırlı tut; dönüş sinyaline göre ikinci temas planla.",
        "İletişim sıklığını düşük tutarak pasif müşteriyi yormadan yeniden dene.",
    ]),
    (1.5, 2.5, "İndirim teklifleri", [
        "Fiyat hassasiyetini tetikleyecek süreli indirim veya kupon sun.",
        "Sepete dönüş ve ikinci alışveriş kampanyalarını öne çıkar.",
        "Düşük marjlı genel indirim yerine kategori bazlı kontrollü teklif kullan.",
        "Teklif performansını dönüşüm ve kampanya maliyetiyle birlikte izle.",
    ]),
    (2.5, 3.5, "Çapraz satış önerileri", [
        "Satın alma geçmişine tamamlayıcı ürün ve paket önerileri ekle.",
        "Ortalama sepet tutarını artıracak birlikte al senaryoları tasarla.",
        "Önerileri müşterinin son kategori ilgisiyle uyumlu hale getir.",
        "Dönüşüm sağlamayan ürünleri otomatik olarak daha düşük önceliğe al.",
    ]),
    (3.5, 4.5, "Kişiselleştirilmiş öneriler", [
        "Geçmiş davranışa göre kişiye özel ürün, kategori ve zamanlama önerisi üret.",
        "Sadakat programı, erken erişim ve özel kampanya iletişimi kullan.",
        "Önerileri e-posta, uygulama içi alan ve web vitrini boyunca tutarlı göster.",
        "Müşteri değerini korumak için gereksiz indirim yerine alaka düzeyini artır.",
    ]),
    (4.5, 5.0, "VIP / premium teklifler", [
        "Premium ürünler, özel koleksiyonlar ve yüksek değerli paketler öner.",
        "VIP sadakat avantajları, öncelikli destek veya erken erişim sun.",
        "Yüksek değerli müşterilerde deneyim kalitesini ve memnuniyeti yakından izle.",
        "Marjı koruyan ayrıcalıklar kullan; indirimi ana strateji yapma.",
    ]),
]

PRM_SEGMENT_DEFINITIONS = [
    (0.0, 1.5, "Pasif kullanıcı yeniden kazanım", [
        "Kısa ve net yeniden etkileşim mesajlarıyla kullanıcıyı geri çağır.",
        "İlk tıklamayı kolaylaştıracak popüler kategori veya son görüntülenen içerik öner.",
        "Düşük etkileşimli kullanıcıya yoğun kişiselleştirme yerine basit akış sun.",
        "Geri dönüş olmazsa iletişim sıklığını azaltıp farklı içerik başlığı test et.",
    ]),
    (1.5, 2.5, "Düşük etkileşim kullanıcıları", [
        "Kullanıcının ilgisini ölçmek için kısa, anlaşılır ve düşük eforlu içerikler göster.",
        "Düşük riskli indirim, kupon veya ücretsiz kargo gibi kampanya tetikleyicileri dene.",
        "Sayfa gezinmesini artıracak kategori kartları ve başlangıç önerileri sun.",
        "Etkileşim alanlarını sadeleştir; gereksiz adımları azalt.",
    ]),
    (2.5, 3.5, "Keşif ve kategori odaklı kullanıcılar", [
        "Benzer kullanıcı davranışlarından türetilmiş kategori ve ürün önerileri göster.",
        "Gezilen sayfalara göre devam içerikleri ve tamamlayıcı keşif akışları oluştur.",
        "Kararsız kullanıcı için karşılaştırma, yorum ve öne çıkan faydaları görünür yap.",
        "İlgi sinyali güçlenen kategorileri sonraki oturumda daha üst sıraya taşı.",
    ]),
    (3.5, 4.5, "Kişiselleştirilmiş yüksek potansiyelli kullanıcılar", [
        "Oturum ve sayfa davranışına göre dinamik kişiselleştirilmiş akış sun.",
        "İlgi duyulan kategorilerde daha derin içerik, ürün ve kampanya önerileri üret.",
        "Kullanıcının etkileşim ritmine uygun bildirim veya e-posta zamanlaması seç.",
        "Yüksek etkileşimi satın alma veya üyelik hedeflerine bağlayacak net çağrılar ekle.",
    ]),
    (4.5, 5.0, "VIP ve premium kullanıcılar", [
        "Yüksek ilgiyi beslemek için premium ürün, yeni kategori ve trend içerikler öner.",
        "VIP kampanya, erken erişim veya özel koleksiyon akışları sun.",
        "Özel koleksiyon, erken erişim veya gelişmiş filtrelerle deneyimi zenginleştir.",
        "Premium önerilerin tekrar ziyaret, sepet değeri ve dönüşüm etkisini ayrı ölç.",
    ]),
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
    prm_mapping = {
        key: _find_column(cols, aliases)
        for key, aliases in PRM_COLUMN_ALIASES.items()
    }
    prm_required_keys = ['customer_id_col', 'category_col', 'session_col', 'pages_col', 'rating_col', 'amount_col']
    prm_score = sum(bool(prm_mapping[key]) for key in prm_required_keys)

    mapping = {
        key: _find_column(cols, aliases)
        for key, aliases in RFM_COLUMN_ALIASES.items()
    }

    has_prm_core = prm_score == len(prm_required_keys)
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
        'prm_mapping': prm_mapping,
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


def process_prm_data(df, mapping=None):
    """
    PRM feature engineering:
    P: 0.5 * entropy + 0.3 * diversity + 0.2 * (1 - dominant ratio)
    R: 0.7 * interaction_depth + 0.3 * avg_rating
    M: log(1 + Total_Amount)
    """
    work_df = df.copy()
    if mapping is None:
        mapping = detect_dataset_structure(work_df)['prm_mapping']

    required_keys = ['customer_id_col', 'category_col', 'session_col', 'pages_col', 'rating_col', 'amount_col']
    missing = [key for key in required_keys if not mapping.get(key)]
    if missing:
        readable = {
            'customer_id_col': 'Müşteri_ID',
            'category_col': 'Product_Category',
            'session_col': 'Session Duration',
            'pages_col': 'Pages Viewed',
            'rating_col': 'Customer Rating',
            'amount_col': 'Total Amount',
        }
        raise ValueError(
            "PRM analizi için eksik sütunlar: " +
            ', '.join(readable[key] for key in missing)
        )

    customer_col = mapping['customer_id_col']
    category_col = mapping['category_col']
    session_col = mapping['session_col']
    pages_col = mapping['pages_col']
    rating_col = mapping['rating_col']
    amount_col = mapping['amount_col']

    numeric_cols = [session_col, pages_col, rating_col, amount_col]
    for col in numeric_cols:
        work_df[col] = pd.to_numeric(work_df[col], errors='coerce')

    subset = [customer_col, category_col, session_col, pages_col, rating_col, amount_col]
    work_df = work_df.dropna(subset=subset)

    work_df['Interaction_Depth'] = work_df[pages_col] / work_df[session_col].replace(0, np.nan)
    work_df['Interaction_Depth'] = work_df['Interaction_Depth'].replace([np.inf, -np.inf], np.nan)
    work_df['Interaction_Depth'] = work_df['Interaction_Depth'].fillna(0)
    work_df['Monetary_Source'] = work_df[amount_col]

    category_counts = (
        work_df
        .groupby([customer_col, category_col])
        .size()
        .rename('Category_Count')
        .reset_index()
    )
    category_summary = category_counts.groupby(customer_col).agg(
        Category_Diversity=(category_col, 'nunique'),
        Dominant_Category_Count=('Category_Count', 'max'),
        Total_Category_Interactions=('Category_Count', 'sum'),
    ).reset_index()
    category_counts = category_counts.merge(
        category_summary[[customer_col, 'Total_Category_Interactions']],
        on=customer_col,
        how='left'
    )
    category_counts['Category_Probability'] = (
        category_counts['Category_Count'] /
        category_counts['Total_Category_Interactions']
    )
    entropy_summary = category_counts.assign(
        Entropy_Component=lambda x: -x['Category_Probability'] * np.log(x['Category_Probability'])
    ).groupby(customer_col)['Entropy_Component'].sum().reset_index(name='Category_Entropy')
    category_summary = category_summary.merge(entropy_summary, on=customer_col, how='left')
    category_summary['Dominant_Category_Ratio'] = (
        category_summary['Dominant_Category_Count'] /
        category_summary['Total_Category_Interactions']
    )
    category_summary = category_summary.rename(columns={customer_col: 'CustomerID'})

    prm = work_df.groupby(customer_col).agg({
        category_col: lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0],
        session_col: 'mean',
        pages_col: 'mean',
        rating_col: 'mean',
        'Interaction_Depth': 'mean',
        'Monetary_Source': 'sum',
    }).reset_index()

    prm.columns = [
        'CustomerID',
        'Preferred_Category',
        'Avg_Session',
        'Avg_Pages',
        'Avg_Rating',
        'interaction_depth',
        'Monetary_Raw',
    ]
    prm = prm.merge(category_summary, on='CustomerID', how='left')
    prm['Inverse_Dominant_Ratio'] = 1 - prm['Dominant_Category_Ratio']

    scaler = MinMaxScaler()
    prm[[
        'Category_Entropy_Norm',
        'Category_Diversity_Norm',
        'Inverse_Dominant_Ratio_Norm',
        'Interaction_Depth_Norm',
        'Rating_Norm',
    ]] = scaler.fit_transform(prm[[
        'Category_Entropy',
        'Category_Diversity',
        'Inverse_Dominant_Ratio',
        'interaction_depth',
        'Avg_Rating',
    ]])

    prm['preference_raw'] = (
        0.5 * prm['Category_Entropy_Norm'] +
        0.3 * prm['Category_Diversity_Norm'] +
        0.2 * prm['Inverse_Dominant_Ratio_Norm']
    )
    prm['engagement_score'] = (
        0.7 * prm['Interaction_Depth_Norm'] +
        0.3 * prm['Rating_Norm']
    )
    prm['monetary_log'] = np.log1p(prm['Monetary_Raw'])
    prm[['preference_score', 'monetary_score']] = scaler.fit_transform(prm[[
        'preference_raw',
        'monetary_log',
    ]])

    prm = prm[[
        'CustomerID',
        'Preferred_Category',
        'Category_Diversity',
        'Dominant_Category_Ratio',
        'Category_Entropy',
        'interaction_depth',
        'preference_score',
        'engagement_score',
        'monetary_score',
        'Monetary_Raw',
        'monetary_log',
    ]]

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


def find_optimal_k(data_transposed, k_min=2, k_max=6):
    """
    Fuzzy C-Means için optimal K sayısını FPC + silhouette skoruna göre bulur.
    """
    n_samples = data_transposed.shape[1]
    k_max = min(k_max, n_samples)
    if n_samples < k_min:
        raise ValueError("Kümeleme için en az 2 müşteri kaydı gereklidir.")

    data_scaled = data_transposed.T
    best_k = 3
    best_hybrid_score = -1

    for k in range(k_min, k_max + 1):
        cntr, u, d, fpc = _fuzzy_cmeans(data_transposed, c=k, m=2, error=0.005, maxiter=500)
        labels = np.argmax(u, axis=0)
        unique_labels = np.unique(labels)
        if 1 < len(unique_labels) < n_samples:
            sil = silhouette_score(data_scaled, labels)
        else:
            sil = -1.0
        silhouette_norm = (sil + 1) / 2
        hybrid_score = (fpc + silhouette_norm) / 2

        if hybrid_score > best_hybrid_score:
            best_hybrid_score = hybrid_score
            best_k = k

    return best_k


def _cluster_desirability_values(centers_df, dataset_type, feature_cols):
    available_cols = [col for col in feature_cols if col in centers_df.columns]
    if not available_cols:
        return pd.Series(np.zeros(len(centers_df)), index=centers_df.index)

    center_values = centers_df[available_cols].astype(float)
    std = center_values.std(ddof=0).replace(0, 1)
    normalized = (center_values - center_values.mean()) / std

    if dataset_type == 'RFM' and 'Recency' in normalized.columns:
        normalized['Recency'] = -normalized['Recency']

    return normalized.mean(axis=1)


def _cluster_scores_from_centers(centers_df, dataset_type, feature_cols):
    desirability = _cluster_desirability_values(centers_df, dataset_type, feature_cols)
    score_df = centers_df[['Cluster']].copy()
    score_df['Centroid_Value'] = desirability.astype(float)
    score_df['Centroid_Rank'] = score_df['Centroid_Value'].rank(
        method='first',
        ascending=True
    ).astype(int)
    k = len(score_df)
    score_df['Cluster_Score'] = (score_df['Centroid_Rank'] / k) * 5
    return score_df


def _get_segment_definition(score, dataset_type):
    definitions = PRM_SEGMENT_DEFINITIONS if dataset_type == 'PRM' else RFM_SEGMENT_DEFINITIONS
    bounded_score = min(max(float(score), 0.0), 5.0)
    for lower, upper, label, items in definitions:
        if lower <= bounded_score < upper or (bounded_score == 5.0 and upper == 5.0):
            return label, items
    return definitions[-1][2], definitions[-1][3]


def _level(value, low, high, invert=False):
    if invert:
        if value <= low:
            return 'high'
        if value >= high:
            return 'low'
        return 'mid'
    if value >= high:
        return 'high'
    if value <= low:
        return 'low'
    return 'mid'


def _quantile_thresholds(centers_df, feature):
    if feature not in centers_df.columns:
        return 0.0, 0.0
    return (
        float(centers_df[feature].quantile(0.33)),
        float(centers_df[feature].quantile(0.67)),
    )


def _semantic_strategy(segment_name):
    strategies = {
        'Yeni müşteri': (
            'İlk Deneyimi Güçlendirme Stratejisi',
            [
                'Hoş geldin kampanyası ve ikinci alışveriş teşviki sun.',
                'Marka güvenini artıran popüler ürün ve yorum içeriklerini göster.',
                'İlk alışveriş kategorisine göre düşük bariyerli öneriler hazırla.',
                'Yeni müşterinin tekrar ziyaret zamanlamasını e-posta veya bildirimle destekle.',
            ],
        ),
        'Sadık müşteri': (
            'Sadakat ve Tekrar Satın Alma Stratejisi',
            [
                'Sadakat puanı, özel kupon veya erken erişim avantajları sun.',
                'Geçmiş alışveriş kategorilerine göre kişiselleştirilmiş ürün öner.',
                'Tekrar satın alma döngüsüne uygun hatırlatma kampanyaları planla.',
                'Memnuniyet ve sepet değeri trendini düzenli izle.',
            ],
        ),
        'Pasif müşteri': (
            'Yeniden Kazanım ve Aktivasyon Stratejisi',
            [
                'Zaman sınırlı geri dönüş kampanyası uygula.',
                'Önceden ilgilenilen kategorileri ve düşük fiyatlı ürünleri tekrar öner.',
                'Push notification ve e-posta ile düşük frekanslı hatırlatma gönder.',
                'Dönüş olmazsa iletişim sıklığını azaltıp farklı teklif test et.',
            ],
        ),
        'VIP müşteri': (
            'Premium Sadakat ve Özel Teklif Stratejisi',
            [
                'Premium ürün ve yüksek değerli bundle önerileri sun.',
                'Erken erişim, özel koleksiyon veya VIP avantajları göster.',
                'Düşük oranlı kişisel indirimlerle marjı koruyarak değer yarat.',
                'Yüksek değerli müşterilerde deneyim kalitesini yakından izle.',
            ],
        ),
        'Fırsat odaklı müşteri': (
            'Kontrollü Kampanya ve Sepet Artırma Stratejisi',
            [
                'Süreli indirim ve kuponları kategori bazlı sınırlandır.',
                'Düşük tutarlı alışverişleri tamamlayıcı ürünlerle büyüt.',
                'Kampanya maliyeti ve dönüşüm oranını birlikte takip et.',
                'İndirim bağımlılığını azaltmak için değer odaklı paketler sun.',
            ],
        ),
        'Explorer kullanıcı': (
            'Kategori Keşfi ve Cross-Sell Stratejisi',
            [
                'Yeni kategori ürünlerini öne çıkar.',
                'Trend ürün önerileri ve keşif rafları sun.',
                'Çapraz kategori kampanyaları göster.',
                'Keşif odaklı kişiselleştirilmiş içerikler öner.',
            ],
        ),
        'Active Browser': (
            'Etkileşimi Dönüşüme Çevirme Stratejisi',
            [
                'Gezilen ürünleri karşılaştırma ve yorum içerikleriyle destekle.',
                'Oturum içi davranışa göre anlık kategori önerileri göster.',
                'Düşük tutarlı teşviklerle ilk dönüşümü kolaylaştır.',
                'Kararsızlığı azaltacak stok, teslimat ve avantaj bilgilerini görünür yap.',
            ],
        ),
        'VIP kullanıcı': (
            'Premium Sadakat ve Özel Teklif Stratejisi',
            [
                'Premium ürün önerileri sun.',
                'Erken erişim kampanyaları göster.',
                'Düşük oranlı özel VIP indirimleri uygula.',
                'Kişiselleştirilmiş premium bundle önerileri üret.',
            ],
        ),
        'Passive kullanıcı': (
            'Yeniden Kazanım ve Aktivasyon Stratejisi',
            [
                'Zaman sınırlı indirim kampanyaları uygula.',
                'Düşük fiyatlı ürün önerileri sun.',
                'Push notification ve e-posta kampanyaları gönder.',
                'Önceden ilgilenilen kategorileri tekrar öner.',
            ],
        ),
        'Engaged kullanıcı': (
            'Etkileşim Derinleştirme Stratejisi',
            [
                'İlgili kategorilerde daha derin içerik ve ürün önerileri sun.',
                'Davranış ritmine uygun bildirim ve kampanya zamanlaması seç.',
                'Orta değerli kullanıcıyı sepet büyütmeye yönlendiren paketler göster.',
                'Etkileşim sinyalini satın alma hedeflerine bağlayan net çağrılar kullan.',
            ],
        ),
        'Selective Premium kullanıcı': (
            'Seçici Premium Dönüşüm Stratejisi',
            [
                'Az ama yüksek değerli tercihlere uygun premium ürünler öner.',
                'Kategori odağını bozmadan özel koleksiyon ve bundle sun.',
                'Genel kampanya yerine kişisel ve sınırlı avantajlar kullan.',
                'Yüksek harcama eğilimini deneyim kalitesiyle destekle.',
            ],
        ),
    }
    return strategies[segment_name]


def _semantic_segment_from_centroid(row, centers_df, dataset_type):
    if dataset_type == 'PRM':
        p_low, p_high = _quantile_thresholds(centers_df, 'preference_score')
        r_low, r_high = _quantile_thresholds(centers_df, 'engagement_score')
        m_low, m_high = _quantile_thresholds(centers_df, 'monetary_score')
        p = _level(float(row['preference_score']), p_low, p_high)
        r = _level(float(row['engagement_score']), r_low, r_high)
        m = _level(float(row['monetary_score']), m_low, m_high)

        if p == 'high' and r == 'high' and m == 'high':
            return 'VIP kullanıcı'
        if p == 'low' and r == 'low' and m == 'low':
            return 'Passive kullanıcı'
        if p == 'low' and m == 'high':
            return 'Selective Premium kullanıcı'
        if p == 'high' and m in ['low', 'mid']:
            return 'Explorer kullanıcı'
        if r == 'high' and m == 'low':
            return 'Active Browser'
        if r == 'high' and m == 'mid':
            return 'Engaged kullanıcı'
        if m == 'high':
            return 'VIP kullanıcı'
        if r == 'high':
            return 'Active Browser'
        if p == 'high':
            return 'Explorer kullanıcı'
        return 'Passive kullanıcı'

    r_low, r_high = _quantile_thresholds(centers_df, 'Recency')
    f_low, f_high = _quantile_thresholds(centers_df, 'Frequency')
    m_low, m_high = _quantile_thresholds(centers_df, 'Monetary')
    recency = _level(float(row['Recency']), r_low, r_high, invert=True)
    frequency = _level(float(row['Frequency']), f_low, f_high)
    monetary = _level(float(row['Monetary']), m_low, m_high)

    if monetary == 'high' and frequency == 'high':
        return 'VIP müşteri'
    if recency == 'high' and frequency == 'high' and monetary == 'high':
        return 'Sadık müşteri'
    if recency == 'low' and frequency == 'low' and monetary == 'low':
        return 'Yeni müşteri'
    if recency == 'high' and frequency == 'low' and monetary == 'low':
        return 'Pasif müşteri'
    if frequency == 'high' and monetary == 'low':
        return 'Fırsat odaklı müşteri'
    if recency == 'high':
        return 'Sadık müşteri'
    if monetary == 'high':
        return 'VIP müşteri'
    return 'Pasif müşteri'


def apply_fuzzy_scores(results, centers_df, membership_matrix, dataset_type, feature_cols):
    cluster_score_df = _cluster_scores_from_centers(centers_df, dataset_type, feature_cols)
    cluster_scores = (
        cluster_score_df
        .sort_values('Cluster')['Cluster_Score']
        .to_numpy(dtype=float)
    )

    weighted_scores = membership_matrix.T @ cluster_scores
    score_col = 'PRM_Score' if dataset_type == 'PRM' else 'RFM_Score'

    scored_results = results.copy()
    scored_results[score_col] = weighted_scores
    scored_results['Final_Score'] = weighted_scores
    scored_results['FinalScore'] = weighted_scores

    labels = []
    recommendation_titles = []
    recommendation_lists = []
    for score in weighted_scores:
        label, items = _get_segment_definition(score, dataset_type)
        labels.append(label)
        recommendation_titles.append(label)
        recommendation_lists.append(' | '.join(items))

    scored_results['Segment_Label'] = labels
    scored_results['Recommendation_Title'] = recommendation_titles
    scored_results['Recommendation_List'] = recommendation_lists

    return scored_results, cluster_score_df


def run_fuzzy_cmeans(data, n_clusters, feature_cols=None, dataset_type='RFM'):
    """
    Belirli bir K değeri için Fuzzy C-Means çalıştırır ve sonuçları döner.
    """
    if feature_cols is None:
        feature_cols = get_feature_columns(dataset_type)
    max_clusters = min(6, len(data))
    if max_clusters < 2:
        raise ValueError("Kümeleme için en az 2 müşteri kaydı gereklidir.")
    n_clusters = int(min(max(n_clusters, 2), max_clusters))

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
    results, cluster_score_df = apply_fuzzy_scores(results, centers_df, u, dataset_type, feature_cols)
    centers_df = centers_df.merge(cluster_score_df, on='Cluster', how='left')
    centers_df = centers_df.sort_values('Centroid_Rank').reset_index(drop=True)

    try:
        silhouette_avg = silhouette_score(data_scaled, cluster_labels)
    except Exception:
        silhouette_avg = 0.0

    return results, centers_df, silhouette_avg, fpc


def get_cluster_recommendations(results_with_clusters, centers_df, dataset_type='RFM'):
    """
    Cluster centroid değerlerini semantik olarak yorumlayıp segment adı ve strateji üretir.
    """
    recommendations = {}
    feature_cols = get_feature_columns(dataset_type)
    score_col = 'PRM_Score' if dataset_type == 'PRM' else 'RFM_Score'

    for _, row in centers_df.iterrows():
        cluster_id = int(row['Cluster'])
        cluster_rows = results_with_clusters[
            results_with_clusters['Cluster'].astype(int) == cluster_id
        ]
        count = len(cluster_rows)
        cluster_score = float(row['Cluster_Score']) if 'Cluster_Score' in row.index else 0.0
        segment_name = _semantic_segment_from_centroid(row, centers_df, dataset_type)
        strategy_title, recs = _semantic_strategy(segment_name)

        if count and score_col in cluster_rows.columns:
            avg_final_score = float(cluster_rows['Final_Score'].mean())
        else:
            avg_final_score = cluster_score

        description = (
            f"Bu cluster {dataset_type} centroid değerlerine göre '{segment_name}' davranış tipini gösterir. "
            f"Centroid tabanlı dinamik skor {cluster_score:.2f}, ortalama fuzzy final skor {avg_final_score:.2f}."
        )
        metrics = {
            feature: float(row[feature])
            for feature in feature_cols
            if feature in row.index
        }
        if 'Monetary' in row.index and 'Monetary' not in metrics:
            metrics['Monetary'] = float(row['Monetary'])

        recommendations[cluster_id] = {
            'name': segment_name,
            'segment_name': segment_name,
            'strategy_title': strategy_title,
            'description': description,
            'recommendations': recs,
            'cautions': [
                "Segment kararı sert küme atamasına değil, tüm üyelik değerlerinin ağırlıklı skoruna dayanır.",
                "K değiştiğinde yalnızca küme sayısı değişir; skor aralıkları ve karar mantığı aynı kalır.",
            ],
            'rec': '\n\n'.join(f"• {item}" for item in recs),
            'count': count,
            'metrics': metrics,
            'cluster_score': cluster_score,
            'avg_final_score': avg_final_score,
            'centroid_rank': int(row['Centroid_Rank']) if 'Centroid_Rank' in row.index else 0,
            'centroid_value': float(row['Centroid_Value']) if 'Centroid_Value' in row.index else 0.0,
        }

    return recommendations
