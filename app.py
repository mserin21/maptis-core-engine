import streamlit as st
import json
import folium
import pandas as pd
from streamlit_folium import st_folium
import base64

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="MAPTİS | Decision Support", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #ffffff; }
    .stSlider [data-baseweb="slider"] { margin-bottom: 20px; }
    .metric-card { background: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .status-badge { padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. VERİ YÜKLEME ---
try:
    with open('data_input.json', 'r', encoding='utf-8') as f:
        parsel_listesi = json.load(f)
except:
    st.error("Veri dosyası bulunamadı!")
    st.stop()

# --- 3. SIDEBAR: STRATEJİK PARAMETRELER ---
st.sidebar.markdown("<h2 style='color:#58a6ff;'>M.A.P.T.İ.S v0.2</h2>", unsafe_allow_html=True)
st.sidebar.write("---")
st.sidebar.subheader("💹 Piyasa Simülasyonu")
maliyet_endeksi = st.sidebar.slider("İnşaat Maliyet Artışı (%)", 0, 200, 45, help="Yıllık beklenen maliyet artış oranı")
deger_artis_hizi = st.sidebar.slider("Gayrimenkul Değer Artışı (%)", 0, 300, 80, help="Bölgedeki yıllık ortalama değer artışı")
dolar_kuru = st.sidebar.number_input("Tahmini Dolar Kuru (Yıl Sonu)", 30.0, 100.0, 45.5)

# --- 4. ANALİZ MOTORU v0.2 ---
def analyze_asset(data, m_index, d_speed):
    area = float(data['parsel_alani'])
    kaks = float(data['kaks'])
    arsa_m2 = float(data['m2_fiyat'])
    
    # Mevcut Durum
    current_land_val = area * arsa_m2
    # Simüle Edilmiş Yapım Maliyeti (Maliyet Endeksi Etkisi)
    base_const_m2 = 22000 # 2026 baz fiyat
    sim_const_m2 = base_const_m2 * (1 + m_index/100)
    total_const_val = area * kaks * sim_const_m2
    
    # Skorlama (Rasyonel ve Sert)
    # Formül: (Konum Skoru * 0.4) + (İmar Verimliliği * 0.4) - (Maliyet Riski * 0.2)
    mali_risk = (m_index / 2)
    score = (int(data['konum_skoru']) * 0.4) + (kaks * 20) - mali_risk
    if "Tarla" in data['tip']: score -= 30
    
    score = max(5, min(97, score))
    
    return {
        "score": score,
        "land_val": current_land_val,
        "const_val": total_const_val,
        "total_cap": current_land_val + total_const_val,
        "future_val": (current_land_val * (1 + d_speed/100))
    }

# --- 5. ANA EKRAN ---
nav = st.sidebar.radio("MENÜ", ["📊 Portföy Analizi", "🎯 Senaryo Testi"])

if nav == "📊 Portföy Analizi":
    st.title("💼 Varlık Havuzu Stratejik Görünüm")
    
    # Özet Metrikler
    total_m2 = sum(p['parsel_alani'] for p in parsel_listesi)
    st.columns(3)[0].metric("Toplam Yönetilen Alan", f"{total_m2:,.0f} m²")
    st.columns(3)[1].metric("Varlık Adedi", f"{len(parsel_listesi)} Parsel")
    st.columns(3)[2].metric("Risk Seviyesi", "Orta-Yüksek", delta="-12%", delta_color="inverse")

    # Renkli Harita
    m = folium.Map(location=[38.67, 29.40], zoom_start=13, tiles="CartoDB dark_matter")
    for p in parsel_listesi:
        res = analyze_asset(p, maliyet_endeksi, deger_artis_hizi)
        color = "green" if res['score'] > 70 else "orange" if res['score'] > 45 else "red"
        folium.CircleMarker([p['lat'], p['lon']], radius=10, color=color, fill=True, popup=p['ada_parsel']).add_to(m)
    st_folium(m, width=None, height=450, use_container_width=True)

else:
    secilen = st.selectbox("Analiz Edilecek Varlık:", [p['ada_parsel'] for p in parsel_listesi])
    data = next(item for item in parsel_listesi if item["ada_parsel"] == secilen)
    res = analyze_asset(data, maliyet_endeksi, deger_artis_hizi)
    
    # KARAR EKRANI
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st.write("### 🚨 Stratejik Karar")
        st.markdown(f"""
            <div style="background:{'#238636' if res['score']>70 else '#da3633'}22; padding:30px; border-radius:15px; border:2px solid {'#238636' if res['score']>70 else '#da3633'}; text-align:center;">
                <h1 style="margin:0; font-size:60px;">%{res['score']:.0f}</h1>
                <p style="font-weight:bold; font-size:20px;">GÜVEN SKORU</p>
                <hr>
                <p>{'YATIRIMA UYGUN: Likidite ve imar dengesi pozitif.' if res['score']>70 else 'RİSKLİ: Mevcut maliyet artışı kârlılığı eritiyor.'}</p>
            </div>
        """, unsafe_allow_html=True)

    with c2:
        st.write("### 💰 Finansal Simülasyon (Simulated ROI)")
        f1, f2 = st.columns(2)
        f1.metric("Arsa Değeri", f"{res['land_val']/1e6:.2f}M TL")
        f1.metric("Yıl Sonu Tahmini Değer", f"{res['future_val']/1e6:.2f}M TL", delta=f"%{deger_artis_hizi}")
        f2.metric("Simüle Yapım Maliyeti", f"{res['const_val']/1e6:.2f}M TL")
        f2.metric("Toplam Sermaye İhtiyacı", f"{res['total_cap']/1e6:.2f}M TL")

    st.write("---")
    st.write("### 📈 Hassasiyet Analizi (Enflasyon Karşısında Varlık)")
    # Basit bir stres testi grafiği
    stres_testi = pd.DataFrame({
        "Senaryo": ["Normal", "Yüksek Maliyet", "Düşük Değerleme", "Kriz Senaryosu"],
        "Skor": [res['score'], res['score']*0.8, res['score']*0.7, res['score']*0.4]
    }).set_index("Senaryo")
    st.bar_chart(stres_testi)
    
    st.write("### 📝 Rasyonel Yönetici Notu")
    st.warning(f"Dikkat: Bu parsel için inşaat maliyet endeksi %{maliyet_endeksi} olarak girilmiştir. Eğer maliyetler bu seviyenin üzerine çıkarsa, projenin başabaş noktası tehlikeye girebilir. {data['jeoloji']} zemin yapısı nedeniyle temel maliyetlerinde %15 sapma payı bırakılmalıdır.")