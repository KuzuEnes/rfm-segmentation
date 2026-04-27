import streamlit as st

st.set_page_config(
    page_title="RFM & Fuzzy K-Means Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from segmentation import process_data, find_optimal_k, run_fuzzy_cmeans, get_cluster_recommendations

# --------------------------------------------------------------------------- #
# Session-state başlangıç değerleri                                            #
# --------------------------------------------------------------------------- #
if 'results_ready' not in st.session_state:
    st.session_state['results_ready'] = False

# --------------------------------------------------------------------------- #
# Başlık                                                                       #
# --------------------------------------------------------------------------- #
st.title("🚀 Akıllı Müşteri Segmentasyonu")
st.markdown(
    "RFM Analizi ve Bulanık K-Means (Fuzzy C-Means) algoritması kullanılarak "
    "verilerinizin segmentasyonunu gerçekleştirin."
)

# --------------------------------------------------------------------------- #
# Sidebar                                                                      #
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown("## 📊 Müşteri Analitiği")
    st.markdown("*Yapay Zeka Destekli Segmentasyon*")
    st.divider()
    st.header("⚙️ Veri Yükleme")
    uploaded_file = st.file_uploader("CSV Dosyanızı Yükleyin", type=['csv'])

if uploaded_file is not None:
    # Dosyayı oku (her render'da hafif)
    uploaded_file.seek(0)
    df = pd.read_csv(uploaded_file)
    cols = df.columns.tolist()

    with st.expander("🔍 Veri Seti Özeti ve Önizleme", expanded=False):
        c1, c2 = st.columns(2)
        c1.metric("Toplam Satır", f"{len(df):,}")
        c2.metric("Sütun Sayısı", len(cols))
        st.dataframe(df.head(), use_container_width=True)

    with st.sidebar.expander("🛠️ Gelişmiş Ayarlar", expanded=False):
        st.markdown("**Sütun Eşleştirme**")
        customer_id_col  = st.selectbox("Müşteri ID Sütunu", cols,
            index=cols.index('Customer ID') if 'Customer ID' in cols else 0)
        invoice_date_col = st.selectbox("Tarih Sütunu", cols,
            index=cols.index('InvoiceDate') if 'InvoiceDate' in cols else 0)
        quantity_col     = st.selectbox("Miktar Sütunu", cols,
            index=cols.index('Quantity') if 'Quantity' in cols else 0)
        price_col        = st.selectbox("Fiyat Sütunu", cols,
            index=cols.index('Price') if 'Price' in cols else 0)
        st.divider()
        auto_k = st.checkbox("Optimal K'yı Otomatik Bul", value=True)
        if not auto_k:
            manual_k = st.slider("Küme Sayısı (K)", min_value=2, max_value=10, value=3)
        else:
            manual_k = None

    # ----------------------------------------------------------------------- #
    # ANALİZ BUTONU — sonuçlar session_state'e yazılır                        #
    # ----------------------------------------------------------------------- #
    if st.sidebar.button("🚀 Analizi Başlat", use_container_width=True, type="primary"):
        try:
            with st.status("Analiz yürütülüyor...", expanded=True) as status:

                st.write("📦 RFM metrikleri hesaplanıyor...")
                rfm = process_data(df, customer_id_col, invoice_date_col,
                                   quantity_col, price_col)

                scaler = StandardScaler()
                rfm_scaled = scaler.fit_transform(rfm[['Recency', 'Frequency', 'Monetary']])
                rfm_transposed = rfm_scaled.T

                if auto_k:
                    st.write("🔍 Optimal K değeri aranıyor...")
                    k = find_optimal_k(rfm_transposed)
                    st.write(f"💡 Optimal küme sayısı: **K = {k}**")
                else:
                    k = manual_k

                st.write(f"⚙️ Fuzzy C-Means çalıştırılıyor (K={k})...")
                rfm_results, centers_df, sil_score, fpc = run_fuzzy_cmeans(rfm, k)
                recs = get_cluster_recommendations(rfm_results, centers_df)

                # Sonuçları session_state'e kaydet
                st.session_state.update({
                    'results_ready': True,
                    'rfm_results':   rfm_results,
                    'centers_df':    centers_df,
                    'sil_score':     sil_score,
                    'fpc':           fpc,
                    'k':             k,
                    'recs':          recs,
                    'raw_df':        df,
                    'cid_col':       customer_id_col,
                    'idate_col':     invoice_date_col,
                })

                status.update(label="✅ Analiz Tamamlandı!", state="complete", expanded=False)

        except Exception as e:
            st.error(f"Analiz sırasında hata oluştu: {e}")

# --------------------------------------------------------------------------- #
# SONUÇLAR — session_state'ten okunur, sekme değişimlerinde kaybolmaz         #
# --------------------------------------------------------------------------- #
if st.session_state['results_ready']:
    rfm_results = st.session_state['rfm_results']
    centers_df  = st.session_state['centers_df']
    fpc         = st.session_state['fpc']
    k           = st.session_state['k']
    recs        = st.session_state['recs']
    raw_df      = st.session_state['raw_df']
    cid_col     = st.session_state['cid_col']
    idate_col   = st.session_state['idate_col']

    st.markdown("---")
    st.header("📊 Analiz Sonuçları")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Toplam Müşteri",     f"{len(rfm_results):,}")
    m2.metric("Toplam Ciro",        f"₺{rfm_results['Monetary'].sum():,.0f}")
    m3.metric("Müşteri Ort. Değer", f"₺{rfm_results['Monetary'].mean():,.0f}")
    m4.metric("Optimal Küme (K)",   k)
    m5.metric("Model Güveni (FPC)", f"{fpc:.2f}")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 3D Segmentasyon Grafiği",
        "📈 RFM Dağılımları",
        "💡 İşletme Önerileri",
        "🔎 Müşteri Sorgulama"
    ])

    # Küme sütununu string'e çevir (grafik için)
    plot_df = rfm_results.copy()
    plot_df['Cluster'] = plot_df['Cluster'].astype(str)

    # ------------------------------------------------------------------ TAB 1
    with tab1:
        st.subheader("Müşteri Segmentleri — 3D Dağılım")
        fig_3d = px.scatter_3d(
            plot_df, x='Recency', y='Frequency', z='Monetary',
            color='Cluster', opacity=0.75,
            hover_data=['CustomerID'],
            title=f"RFM Küme Dağılımı (K={k})",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_3d.update_layout(margin=dict(l=0, r=0, b=0, t=40), height=600)
        st.plotly_chart(fig_3d, use_container_width=True)

        st.subheader("Küme Merkezleri (Ortalama Değerler)")
        dc = centers_df.copy()
        for col in ['Recency', 'Frequency', 'Monetary']:
            dc[col] = dc[col].round(1)
        cc = plot_df['Cluster'].value_counts().reset_index()
        cc.columns = ['Cluster', 'Müşteri Sayısı']
        cc['Cluster'] = cc['Cluster'].astype(int)
        dc = dc.merge(cc, on='Cluster')
        st.dataframe(dc, use_container_width=True)

    # ------------------------------------------------------------------ TAB 2
    with tab2:
        st.subheader("Recency vs Frequency")
        fig_rf = px.scatter(plot_df, x='Recency', y='Frequency', color='Cluster',
                            hover_data=['CustomerID', 'Monetary'],
                            color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_rf, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Frequency vs Monetary")
            fig_fm = px.scatter(plot_df, x='Frequency', y='Monetary', color='Cluster',
                                color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_fm, use_container_width=True)
        with c2:
            st.subheader("Recency vs Monetary")
            fig_rm = px.scatter(plot_df, x='Recency', y='Monetary', color='Cluster',
                                color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_rm, use_container_width=True)

        st.subheader("Segment Dağılımı")
        seg_counts = plot_df['Cluster'].value_counts().reset_index()
        seg_counts.columns = ['Küme', 'Müşteri Sayısı']
        fig_pie = px.pie(seg_counts, values='Müşteri Sayısı', names='Küme',
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

    # ------------------------------------------------------------------ TAB 3
    with tab3:
        st.subheader("Segment Bazlı Aksiyon Planı")
        for cluster_id, details in recs.items():
            with st.container(border=True):
                st.subheader(f"{details['name']} — Küme {cluster_id} ({details['count']} Müşteri)")
                col_r, col_f, col_m = st.columns(3)
                col_r.metric("Ort. Recency",   f"{details['avg_r']:.1f} gün")
                col_f.metric("Ort. Frequency",  f"{details['avg_f']:.1f} işlem")
                col_m.metric("Ort. Monetary",   f"₺{details['avg_m']:,.1f}")
                st.info(f"**💡 Aksiyon Önerisi:**\n\n{details['rec']}")

        st.divider()
        st.download_button(
            "⬇️ Sonuçları CSV Olarak İndir",
            rfm_results.to_csv(index=False).encode('utf-8'),
            "rfm_segmentation_results.csv",
            "text/csv",
            use_container_width=True
        )

    # ------------------------------------------------------------------ TAB 4
    with tab4:
        st.subheader("Bireysel Müşteri Analizi")
        customer_list     = rfm_results['CustomerID'].astype(str).tolist()
        selected_customer = st.selectbox("Müşteri ID Arayın veya Seçin:",
                                         ["Seçiniz..."] + customer_list)

        if selected_customer != "Seçiniz...":
            cust_row     = rfm_results[rfm_results['CustomerID'].astype(str) == selected_customer].iloc[0]
            cust_cluster = int(float(cust_row['Cluster']))
            cluster_info = recs[cust_cluster]

            st.markdown(f"### 👤 Müşteri Profili: `{selected_customer}`")
            cc1, cc2, cc3, cc4 = st.columns(4)
            cc1.metric("Segment",   cluster_info['name'])
            cc2.metric("Recency",   f"{cust_row['Recency']:.0f} gün önce")
            cc3.metric("Frequency", f"{cust_row['Frequency']:.0f} işlem")
            cc4.metric("Monetary",  f"₺{cust_row['Monetary']:,.0f}")
            st.divider()
            st.success(f"**💡 Stratejik Aksiyon Planı:**\n\n{cluster_info['rec']}")

            st.subheader("Son 10 İşlem")
            hist = raw_df[raw_df[cid_col].astype(str) == selected_customer]
            hist = hist.sort_values(by=idate_col, ascending=False).head(10)
            st.dataframe(hist, use_container_width=True)

else:
    if uploaded_file is None:
        st.info("👈 Lütfen sol panelden bir CSV dosyası yükleyerek başlayın.")
        st.markdown("### Beklenen Veri Formatı")
        st.markdown("""
| Sütun | Açıklama |
|---|---|
| `Customer ID` | Müşteri kimlik numarası |
| `InvoiceDate` | İşlem tarihi |
| `Quantity` | Satın alınan miktar |
| `Price` | Birim fiyat |
        """)
