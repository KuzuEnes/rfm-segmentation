import streamlit as st

st.set_page_config(
    page_title="RFM & Fuzzy K-Means Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================================== #
#  DARK PROFESSIONAL CSS                                                        #
# =========================================================================== #
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Ana arka plan ── */
[data-testid="stAppViewContainer"] {
    background: #0D1117;
}
[data-testid="stMain"] {
    background: #0D1117;
}

/* ── Header (üst bar) ── */
[data-testid="stHeader"] {
    background: rgba(13, 17, 23, 0.95);
    border-bottom: 1px solid rgba(0, 212, 255, 0.15);
    backdrop-filter: blur(10px);
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1117 0%, #161B22 40%, #0D1117 100%);
    border-right: 1px solid rgba(0, 212, 255, 0.2);
}
[data-testid="stSidebar"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #00D4FF, #7C3AED, #00D4FF);
    background-size: 200% 100%;
    animation: shimmer 3s linear infinite;
}
@keyframes shimmer {
    0%   { background-position: -200% 0; }
    100% { background-position:  200% 0; }
}

/* ── Sidebar içerik ── */
[data-testid="stSidebar"] .stMarkdown h2 {
    background: linear-gradient(135deg, #00D4FF, #7C3AED);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 700;
    font-size: 1.2rem;
    letter-spacing: 0.5px;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stCheckbox label {
    color: #8B949E !important;
}

/* ── Başlık (h1) ── */
h1 {
    background: linear-gradient(135deg, #00D4FF 0%, #7C3AED 60%, #00D4FF 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 700 !important;
    font-size: 2.2rem !important;
    animation: textShimmer 4s linear infinite;
    letter-spacing: -0.5px;
}
@keyframes textShimmer {
    0%   { background-position: 0% center; }
    100% { background-position: 200% center; }
}

/* ── Alt açıklama metni ── */
[data-testid="stMarkdownContainer"] p {
    color: #8B949E;
    font-size: 0.95rem;
}

/* ── Metric kartlar — glassmorphism ── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg,
        rgba(0, 212, 255, 0.07) 0%,
        rgba(124, 58, 237, 0.07) 100%);
    border: 1px solid rgba(0, 212, 255, 0.2);
    border-radius: 14px;
    padding: 18px 20px !important;
    backdrop-filter: blur(12px);
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    border-color: rgba(0, 212, 255, 0.55);
    box-shadow: 0 8px 32px rgba(0, 212, 255, 0.15);
}
[data-testid="stMetricLabel"] {
    color: #8B949E !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
[data-testid="stMetricValue"] {
    color: #E6EDF3 !important;
    font-size: 1.65rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] {
    color: #00D4FF !important;
}

/* ── Buton ── */
.stButton > button {
    background: linear-gradient(135deg, #00D4FF, #7C3AED);
    color: #fff !important;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    font-size: 0.9rem;
    letter-spacing: 0.3px;
    padding: 12px 24px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3);
    position: relative;
    overflow: hidden;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0, 212, 255, 0.45);
}
.stButton > button:active {
    transform: translateY(0px);
}

/* ── Tab bar ── */
[data-testid="stTabs"] {
    background: rgba(22, 27, 34, 0.6);
    border-radius: 12px;
    padding: 6px;
    border: 1px solid rgba(0, 212, 255, 0.1);
}
button[data-baseweb="tab"] {
    background: transparent;
    border-radius: 8px;
    color: #8B949E !important;
    font-weight: 500;
    transition: all 0.25s ease;
    border: none !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg,
        rgba(0, 212, 255, 0.2),
        rgba(124, 58, 237, 0.2)) !important;
    color: #00D4FF !important;
    font-weight: 600;
    border: 1px solid rgba(0, 212, 255, 0.3) !important;
}
button[data-baseweb="tab"]:hover {
    color: #E6EDF3 !important;
    background: rgba(255,255,255,0.05) !important;
}
[data-testid="stTabPanel"] {
    background: transparent;
    padding-top: 20px;
}

/* ── st.container(border=True) ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(135deg,
        rgba(22, 27, 34, 0.9),
        rgba(13, 17, 23, 0.9));
    border: 1px solid rgba(0, 212, 255, 0.15) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(10px);
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
    padding: 4px;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(0, 212, 255, 0.35) !important;
    box-shadow: 0 4px 24px rgba(0, 212, 255, 0.08);
}

/* ── st.info / st.success / st.error ── */
[data-testid="stAlertContainer"] {
    border-radius: 10px;
    border-left-width: 4px;
}
.stAlert[data-baseweb="notification"][kind="info"] {
    background: rgba(0, 212, 255, 0.08);
    border-left-color: #00D4FF;
}
.stAlert[data-baseweb="notification"][kind="success"] {
    background: rgba(16, 185, 129, 0.08);
    border-left-color: #10B981;
}
.stAlert[data-baseweb="notification"][kind="error"] {
    background: rgba(239, 68, 68, 0.08);
    border-left-color: #EF4444;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: rgba(22, 27, 34, 0.7);
    border: 1px solid rgba(0, 212, 255, 0.12) !important;
    border-radius: 10px !important;
}
[data-testid="stExpander"]:hover {
    border-color: rgba(0, 212, 255, 0.3) !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(0, 212, 255, 0.15);
    border-radius: 10px;
    overflow: hidden;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: rgba(22, 27, 34, 0.6);
    border: 2px dashed rgba(0, 212, 255, 0.3) !important;
    border-radius: 12px;
    transition: border-color 0.25s, background 0.25s;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(0, 212, 255, 0.7) !important;
    background: rgba(0, 212, 255, 0.04);
}

/* ── Input / Selectbox ── */
[data-baseweb="select"] {
    background: rgba(22, 27, 34, 0.8) !important;
    border-color: rgba(0, 212, 255, 0.2) !important;
    border-radius: 8px !important;
}
[data-baseweb="input"] {
    background: rgba(22, 27, 34, 0.8) !important;
    border-color: rgba(0, 212, 255, 0.2) !important;
    border-radius: 8px !important;
}

/* ── Başlık h2, h3 ── */
h2 {
    color: #E6EDF3 !important;
    font-weight: 600 !important;
    font-size: 1.4rem !important;
}
h3 {
    color: #C9D1D9 !important;
    font-weight: 500 !important;
}

/* ── Divider ── */
hr {
    border-color: rgba(0, 212, 255, 0.15) !important;
}

/* ── Status widget (analiz yürütülüyor...) ── */
[data-testid="stStatusWidget"] {
    background: rgba(22, 27, 34, 0.9);
    border: 1px solid rgba(0, 212, 255, 0.2);
    border-radius: 12px;
}

/* ── Özel scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0D1117; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #00D4FF, #7C3AED);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: #00D4FF; }

/* ── Download butonu ── */
[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, rgba(0,212,255,0.15), rgba(124,58,237,0.15));
    border: 1px solid rgba(0, 212, 255, 0.4) !important;
    color: #00D4FF !important;
    border-radius: 10px;
    font-weight: 600;
    transition: all 0.3s ease;
}
[data-testid="stDownloadButton"] > button:hover {
    background: linear-gradient(135deg, rgba(0,212,255,0.3), rgba(124,58,237,0.3));
    box-shadow: 0 4px 20px rgba(0, 212, 255, 0.25);
    transform: translateY(-2px);
}

/* ── Selectbox dropdown ── */
[data-testid="stSelectbox"] {
    color: #E6EDF3;
}
</style>
""", unsafe_allow_html=True)

import pandas as pd
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from segmentation import process_data, find_optimal_k, run_fuzzy_cmeans, get_cluster_recommendations

# ── Plotly koyu tema şablonu ──────────────────────────────────────────────── #
PLOTLY_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(22,27,34,0.8)',
        font=dict(color='#E6EDF3', family='Inter'),
        xaxis=dict(gridcolor='rgba(0,212,255,0.1)', zerolinecolor='rgba(0,212,255,0.1)'),
        yaxis=dict(gridcolor='rgba(0,212,255,0.1)', zerolinecolor='rgba(0,212,255,0.1)'),
        colorway=['#00D4FF','#7C3AED','#10B981','#F59E0B','#EF4444','#EC4899','#8B5CF6'],
        legend=dict(bgcolor='rgba(22,27,34,0.8)', bordercolor='rgba(0,212,255,0.2)', borderwidth=1),
    )
)

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
# SONUÇLAR                                                                     #
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

    plot_df = rfm_results.copy()
    plot_df['Cluster'] = plot_df['Cluster'].astype(str)

    COLORS = ['#00D4FF','#7C3AED','#10B981','#F59E0B','#EF4444','#EC4899','#8B5CF6']

    # ── TAB 1 ── #
    with tab1:
        st.subheader("Müşteri Segmentleri — 3D Dağılım")
        fig_3d = px.scatter_3d(
            plot_df, x='Recency', y='Frequency', z='Monetary',
            color='Cluster', opacity=0.80,
            hover_data=['CustomerID'],
            title=f"RFM Küme Dağılımı (K={k})",
            color_discrete_sequence=COLORS
        )
        fig_3d.update_layout(
            **PLOTLY_TEMPLATE['layout'],
            margin=dict(l=0, r=0, b=0, t=40),
            height=600,
            scene=dict(
                bgcolor='rgba(13,17,23,0.9)',
                xaxis=dict(gridcolor='rgba(0,212,255,0.12)', color='#8B949E'),
                yaxis=dict(gridcolor='rgba(0,212,255,0.12)', color='#8B949E'),
                zaxis=dict(gridcolor='rgba(0,212,255,0.12)', color='#8B949E'),
            )
        )
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

    # ── TAB 2 ── #
    with tab2:
        st.subheader("Recency vs Frequency")
        fig_rf = px.scatter(
            plot_df, x='Recency', y='Frequency', color='Cluster',
            hover_data=['CustomerID', 'Monetary'],
            color_discrete_sequence=COLORS
        )
        fig_rf.update_layout(**PLOTLY_TEMPLATE['layout'])
        st.plotly_chart(fig_rf, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Frequency vs Monetary")
            fig_fm = px.scatter(plot_df, x='Frequency', y='Monetary', color='Cluster',
                                color_discrete_sequence=COLORS)
            fig_fm.update_layout(**PLOTLY_TEMPLATE['layout'])
            st.plotly_chart(fig_fm, use_container_width=True)
        with c2:
            st.subheader("Recency vs Monetary")
            fig_rm = px.scatter(plot_df, x='Recency', y='Monetary', color='Cluster',
                                color_discrete_sequence=COLORS)
            fig_rm.update_layout(**PLOTLY_TEMPLATE['layout'])
            st.plotly_chart(fig_rm, use_container_width=True)

        st.subheader("Segment Dağılımı")
        seg_counts = plot_df['Cluster'].value_counts().reset_index()
        seg_counts.columns = ['Küme', 'Müşteri Sayısı']
        fig_pie = px.pie(
            seg_counts, values='Müşteri Sayısı', names='Küme',
            hole=0.45, color_discrete_sequence=COLORS
        )
        fig_pie.update_layout(**PLOTLY_TEMPLATE['layout'])
        fig_pie.update_traces(textfont_color='#E6EDF3')
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── TAB 3 ── #
    with tab3:
        st.subheader("Segment Bazlı Aksiyon Planı")
        for cluster_id, details in recs.items():
            with st.container(border=True):
                st.subheader(f"{details['name']} — Küme {cluster_id} ({details['count']} Müşteri)")
                col_r, col_f, col_m = st.columns(3)
                col_r.metric("Ort. Recency",  f"{details['avg_r']:.1f} gün")
                col_f.metric("Ort. Frequency", f"{details['avg_f']:.1f} işlem")
                col_m.metric("Ort. Monetary",  f"₺{details['avg_m']:,.1f}")
                st.info(f"**💡 Aksiyon Önerisi:**\n\n{details['rec']}")

        st.divider()
        st.download_button(
            "⬇️ Sonuçları CSV Olarak İndir",
            rfm_results.to_csv(index=False).encode('utf-8'),
            "rfm_segmentation_results.csv",
            "text/csv",
            use_container_width=True
        )

    # ── TAB 4 ── #
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
