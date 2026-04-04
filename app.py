import streamlit as st
import json
import folium
import pandas as pd
from streamlit_folium import st_folium
import base64

# --- 1. KURUMSAL UI YAPILANDIRMASI ---
st.set_page_config(page_title="MAPTİS | Strategic Analysis", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #ffffff; }
    div[data-testid="stMetric"] { background: #161b22 !important; border: 1px solid #30363d !important; border-radius: 12px !important; padding: 15px !important; }
    .verdict-box { padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 2px solid; text-align: center; }
    .analysis-card { background: #1c2128; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 10px; }
    .stHeader { color: #58a6ff; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. VERİ YÜKLEME ---
try:
    with open('data_input.json', 'r', encoding='utf-8') as f:
        parsel_listesi = json.load(f)
except:
    st.error("Veri dosyası (data_input.json) bulunamadı!")
    st.stop()

# --- 3. ANALİTİK HESAPLAMA MOTORU ---
def run_strategic_engine(data):
    # Finansal Temeller
    area = float(data['parsel_alani'])
    kaks = float(data['kaks'])
    m2_fiyat = float(data['m2_fiyat'])
    
    arsa_degeri = area * m2_fiyat
    insaat_alani = area * kaks
    
    # Yapım Analizi (2026 Birim Fiyatları)
    birim_yapim = 24000 if "Ticaret" in data['tip'] else 21000 if "Konut" in data['tip'] else 0
    toplam_yapim_maliyeti = insaat_alani * birim_yapim
    toplam_proje_maliyeti = arsa_degeri + toplam_yapim_maliyeti
    
    # Güven Skoru Algoritması (Vasıf + Konum + Jeoloji)
    base_score = 85 if "Ticaret" in data['tip'] else 65 if "Konut" in data['tip'] else 30
    score = base_score + (int(data['konum_skoru']) - 50) * 0.4
    if "Sağlam" not in data['jeoloji']: score -= 15
    score = max(5, min(98, score))
    
    # Yatırım Kararı
    if score >= 70: verdict, v_col, v_txt = "YATIRIM YAPILABİLİR", "#238636", "Yüksek getiri ve likidite potansiyeli."
    elif score >= 50: verdict, v_col, v_txt = "DEĞERLENDİRİLEBİLİR", "#d29922", "Stratejik beklemeye veya proje geliştirmeye uygun."
    else: verdict, v_col, v_txt = "RİSKLİ / BEKLENMELİ", "#da3633", "Düşük likidite veya imar kısıtı mevcut."
    
    return {
        "score": score, "verdict": verdict, "color": v_col, "text": v_txt,
        "arsa": arsa_degeri, "yapim": toplam_yapim_maliyeti, "toplam": toplam_proje_maliyeti,
        "insaat_m2": insaat_alani
    }

# --- 4. SIDEBAR NAVİGASYON ---
st.sidebar.markdown("<h2 style='color:#58a6ff;'>M.A.P.T.İ.S</h2>", unsafe_allow_html=True)
nav = st.sidebar.radio("ANALİZ SEVİYESİ", ["🏢 Portföy Keşfi", "🔬 Detaylı Varlık Analizi"])

# --- 5. PORTFÖY KEŞFİ (RENKLİ HARİTA) ---
if nav == "🏢 Portföy Keşfi":
    st.title("🌍 Stratejik Varlık Haritası")
    st.info("Harita Renkleri: Yeşil (Ticaret), Mavi (Konut), Turuncu (Tarla/İmarsız)")
    
    m = folium.Map(location=[38.67, 29.40], zoom_start=13, tiles="CartoDB dark_matter")
    for p in parsel_listesi:
        color = "green" if "Ticaret" in p['tip'] else "blue" if "Konut" in p['tip'] else "orange"
        folium.CircleMarker(
            location=[p['lat'], p['lon']],
            radius=12,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=f"<b>{p['ada_parsel']}</b><br>Tip: {p['tip']}"
        ).add_to(m)
    st_folium(m, width=None, height=550, use_container_width=True)
    st.dataframe(pd.DataFrame(parsel_listesi)[['ada_parsel', 'tip', 'parsel_alani', 'vasif']], use_container_width=True)

# --- 6. DETAYLI VARLIK ANALİZİ ---
else:
    secilen = st.selectbox("Analiz edilecek varlığı seçin:", [p['ada_parsel'] for p in parsel_listesi])
    data = next(item for item in parsel_listesi if item["ada_parsel"] == secilen)
    res = run_strategic_engine(data)

    # Karar Kartı
    st.markdown(f"""
        <div class="verdict-box" style="border-color: {res['color']}; background: {res['color']}11;">
            <h1 style="color: {res['color']}; margin:0;">{res['verdict']}</h1>
            <p style="font-size:24px; margin:5px 0;">MAPTİS Güven Skoru: %{res['score']:.1f}</p>
            <p style="color: #8b949e;">{res['text']}</p>
        </div>
    """, unsafe_allow_html=True)

    # Detay Kolonları
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Arsa Değeri", f"{res['arsa']/1e6:.2f}M TL")
    c2.metric("Yapım Maliyeti", f"{res['yapim']/1e6:.2f}M TL")
    c3.metric("Toplam Yatırım", f"{res['toplam']/1e6:.2f}M TL")
    c4.metric("İnşaat Kapasitesi", f"{res['insaat_m2']:,.0f} m²")

    st.write("---")
    col_l, col_r = st.columns([1.2, 1])

    with col_l:
        st.write("### 🏗️ Yapım ve Yatırım Analizi")
        st.markdown(f"""
        <div class="analysis-card">
            <b>📍 Konum Analizi:</b> {data['vasif']} üzerinde, {data['konum_skoru']} puanlık stratejik erişilebilirlik.<br><br>
            <b>🛠️ Teknik Analiz:</b> {data['jeoloji']} zemin yapısı. {'İnşaat için uygun.' if 'Sağlam' in data['jeoloji'] else 'Ek zemin iyileştirme maliyeti gerekebilir.'}<br><br>
            <b>💰 Maliyet Dağılımı:</b> Toplam yatırımın %{(res['arsa']/res['toplam'])*100:.1f}'i arsa, %{(res['yapim']/res['toplam'])*100:.1f}'i yapı maliyetidir.
        </div>
        """, unsafe_allow_html=True)
        
        # Yatırım Projeksiyon Grafiği
        proj = pd.DataFrame({
            "Yıl": ["Mevcut", "1. Yıl", "3. Yıl", "5. Yıl"],
            "Varlık Değeri (Milyon TL)": [res['arsa']/1e6, (res['arsa']*1.45)/1e6, (res['arsa']*3.2)/1e6, (res['arsa']*6.1)/1e6]
        }).set_index("Yıl")
        st.area_chart(proj)

    with col_r:
        st.write("### 🔍 Detaylı Parsel Verileri")
        with st.expander("📝 İmar ve Mülkiyet Bilgileri", expanded=True):
            st.write(f"**Vasıf:** {data['vasif']}")
            st.write(f"**Emsal (KAKS):** {data['kaks']}")
            st.write(f"**Kat Adedi:** {data['kat_adedi']}")
            st.write(f"**Birim m² Fiyatı:** {data['m2_fiyat']:,} TL")
        
        st.write("### 🧠 Stratejik SWOT")
        s1, s2 = st.columns(2)
        with s1:
            st.success(f"**GÜÇLÜ**\n\n{data['tip']} fonksiyonu ve konum avantajı.")
            st.warning(f"**FIRSAT**\n\nBölgesel kentsel gelişim ve değerleme artışı.")
        with s2:
            st.error(f"**ZAYIF**\n\n{res['yapim']/1e6:.1f}M TL tahmini yapı maliyeti.")
            st.info(f"**TEHDİT**\n\nPiyasa likidite riski ve faiz oranları.")

        # Rapor İndirme
        b64 = base64.b64encode(f"MAPTIS ANALIZ: {secilen}\nSkor: %{res['score']:.1f}\nToplam Yatırım: {res['toplam']/1e6:.2f}M TL".encode()).decode()
        st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="MAPTIS_{data["ada_parsel"].split("/")[0]}.txt" style="display:block; width:100%; text-align:center; padding:10px; background:#21262d; border:1px solid #30363d; border-radius:8px; color:#58a6ff; text-decoration:none; font-weight:bold;">📥 Yatırım Dosyasını İndir</a>', unsafe_allow_html=True)