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

def process_data(df, customer_id_col='Customer ID', invoice_date_col='InvoiceDate',
                 quantity_col='Quantity', price_col='Price'):
    """
    Veriyi temizler ve RFM tablosunu oluşturur.
    """
    df = df[df[customer_id_col].notna()].copy()
    df[invoice_date_col] = pd.to_datetime(df[invoice_date_col])

    if 'TotalPrice' not in df.columns:
        df['TotalPrice'] = df[quantity_col] * df[price_col]

    df['CustomerID'] = df[customer_id_col].astype(str)

    analysis_date = df[invoice_date_col].max() + pd.Timedelta(days=1)

    rfm = df.groupby('CustomerID').agg(
        Recency=(invoice_date_col, lambda x: (analysis_date - x.max()).days),
        Frequency=(invoice_date_col, 'count'),
        Monetary=('TotalPrice', 'sum')
    ).reset_index()

    return rfm


def find_optimal_k(rfm_transposed, k_min=2, k_max=8):
    """
    Fuzzy C-Means için optimal K sayısını bulur (hibrit FPC + PE + XB skoru).
    """
    best_k = 3
    best_hybrid_score = -1

    for k in range(k_min, k_max + 1):
        cntr, u, d, fpc = _fuzzy_cmeans(rfm_transposed, c=k, m=2, error=0.005, maxiter=500)

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


def run_fuzzy_cmeans(rfm, n_clusters):
    """
    Belirli bir K değeri için Fuzzy C-Means çalıştırır ve sonuçları döner.
    """
    scaler = StandardScaler()
    rfm_scaled = scaler.fit_transform(rfm[['Recency', 'Frequency', 'Monetary']])
    rfm_transposed = rfm_scaled.T  # (n_features, n_samples)

    cntr, u, d, fpc = _fuzzy_cmeans(rfm_transposed, c=n_clusters, m=2, error=0.005, maxiter=1000)

    cluster_labels = np.argmax(u, axis=0)
    rfm = rfm.copy()
    rfm['Cluster'] = cluster_labels

    for i in range(n_clusters):
        rfm[f'Membership_C{i}'] = u[i]

    # Küme merkezlerini orijinal ölçeğe çevir
    cluster_centers = scaler.inverse_transform(cntr)
    centers_df = pd.DataFrame(cluster_centers, columns=['Recency', 'Frequency', 'Monetary'])
    centers_df['Cluster'] = range(n_clusters)

    try:
        silhouette_avg = silhouette_score(rfm_scaled, cluster_labels)
    except Exception:
        silhouette_avg = 0.0

    return rfm, centers_df, silhouette_avg, fpc


def get_cluster_recommendations(rfm_with_clusters, centers_df):
    """
    Kümelerin özelliklerine göre iş önerileri üretir.
    """
    recommendations = {}

    for idx, row in centers_df.iterrows():
        cluster_id = int(row['Cluster'])
        r = row['Recency']
        f = row['Frequency']
        m = row['Monetary']

        if r < 100 and f > 50:
            name = "🌟 Sadık Müşteriler (Champions / Loyal Customers)"
            rec = "• VIP müşteri programı oluşturulmalı\n• Özel indirim kuponları sunulmalı\n• Sadakat programı uygulanmalı\n• Premium ürün önerileri yapılmalı"
        elif r < 100 and f <= 20:
            name = "👋 Yeni Müşteriler"
            rec = "• Hoş geldin kampanyası uygulanmalı\n• İlk alışveriş indirimi sunulmalı\n• Marka güveni artırılmalı"
        elif r < 100 and 20 < f <= 50:
            name = "🎯 Potansiyel Sadık Müşteriler"
            rec = "• Cross-sell ve up-sell stratejileri uygulanmalı\n• Paket kampanyaları sunulmalı\n• Sadakat programına dahil edilmeli"
        elif 100 <= r < 250 and f > 20:
            name = "⚠️ Kaybedilme Riski Olanlar (At Risk)"
            rec = "• Geri kazanım kampanyası uygulanmalı\n• Kişiselleştirilmiş e-posta gönderilmeli\n• Özel geri dönüş indirimleri sunulmalı\n• SMS ile hatırlatma yapılmalı"
        elif 100 <= r < 300 and f <= 20:
            name = "💤 Uyuyan Müşteriler"
            rec = "• Re-activation kampanyası yapılmalı\n• Son şans teklifleri sunulmalı"
        else:
            name = "📉 Düşük Değerli Müşteriler"
            rec = "• Düşük maliyetli kampanyalar uygulanmalı\n• Otomatik pazarlama tercih edilmeli"

        count = len(rfm_with_clusters[rfm_with_clusters['Cluster'].astype(int) == cluster_id])

        recommendations[cluster_id] = {
            'name': name,
            'rec': rec.replace('\n', '\n\n'),
            'count': count,
            'avg_r': r,
            'avg_f': f,
            'avg_m': m
        }

    return recommendations
