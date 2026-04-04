import streamlit as st
import json
import folium
import pandas as pd
from streamlit_folium import st_folium
import base64

# --- 1. KURUMSAL UI & THEME ---
st.set_page_config(page_title="MAPTİS | Strategic Investment Engine", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stMetric { background: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 12px; }
    .decision-card { padding: 25px; border-radius: 15px; border: 2px solid; margin-bottom: 25px; }
    .swot-box { padding: 15px; border-radius: 8px; margin-bottom: 10px; font-size: 14px; line-height: 1.4; }
    .s-box { background: rgba(35, 134, 54, 0.1); border-left: 5px solid #238636; }
    .w-box { background: rgba(218, 54, 51, 0.1); border-left: 5px solid #da3633; }
    .o-box { background: rgba(210, 153, 34, 0.1); border-left: 5px solid #d29922; }
    .t-box { background: rgba(139, 148, 158, 0.1); border-left: 5px solid #8b949e; }
    .reason-chip { display: inline-block; padding: 4px 12px; border-radius: 15px; background: #21262d; border: 1px solid #30363d; margin: 4px; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
try:
    with open('data_input.json', 'r', encoding='utf-8') as f:
        parsel_listesi = json.load(f)
except:
    st.error("Hata: 'data_input.json' dosyası okunamadı.")
    st.stop()

# --- 3. SIDEBAR: MARKET SIMULATOR ---
st.sidebar.markdown("<h2 style='color:#58a6ff;'>M.A.P.T.İ.S v1.0</h2>", unsafe_allow_html=True)
st.sidebar.write("---")
st.sidebar.subheader("💹 Piyasa Simülasyonu")
maliyet_artis = st.sidebar.slider("İnşaat Maliyet Artışı (%)", 0, 150, 40)
deger_artis = st.sidebar.slider("Bölgesel Değer Artışı (%)", 0, 200, 75)

# --- 4. STRATEJİK KARAR FONKSİYONU ---
def get_investment_logic(p, score):
    area = float(p['parsel_alani'])
    if score >= 75:
        return {
            "label": "KUVVETLİ AL (STRATEJİK VARLIK)", "color": "#238636",
            "why_yes": ["Yüksek imar verimliliği", "Likidite hızı yüksek", "Merkezi lokasyon avantajı"],
            "why_no": ["Yüksek giriş sermayesi gereksinimi", "Düşük pazarlık marjı"],
            "action": "Derhal satın alma veya geliştirme sürecini başlat."
        }
    elif score >= 55:
        return {
            "label": "İZLE VE DEĞERLENDİR (BEKLE)", "color": "#d29922",
            "why_yes": ["Gelecek vaat eden bölge", "Maliyet/Alan dengesi makul"],
            "why_no": ["Altyapı eksikliği", "Hukuki süreçlerin belirsizliği"],
            "action": "İmar planı netleşene kadar opsiyon sözleşmesiyle bekle."
        }
    else:
        return {
            "label": "YATIRIMDAN KAÇIN (RİSKLİ)", "color": "#da3633",
            "why_yes": ["Düşük birim fiyat avantajı"],
            "why_no": ["Tarım arazisi kısıtı", "Zemin sıvılaşma riski", "Düşük geri dönüş hızı"],
            "action": "Sermayeyi buraya bağlamak yerine likit varlıklarda kal."
        }

# --- 5. ANA SAYFA ---
nav = st.sidebar.radio("NAVİGASYON", ["📊 Portföy Dashboard", "🔍 Derinlemesine Analiz"])

if nav == "📊 Portföy Dashboard":
    st.title("🌍 Stratejik Varlık Dağılımı")
    m = folium.Map(location=[38.67, 29.40], zoom_start=13, tiles="CartoDB dark_matter")
    for p in parsel_listesi:
        score = (int(p['konum_skoru']) * 0.5) + (float(p['kaks']) * 20)
        if "Tarla" in p['tip']: score -= 30
        color = "green" if score > 75 else "orange" if score > 55 else "red"
        folium.CircleMarker([p['lat'], p['lon']], radius=10, color=color, fill=True, popup=p['ada_parsel']).add_to(m)
    st_folium(m, width=None, height=500, use_container_width=True)
    st.dataframe(pd.DataFrame(parsel_listesi)[['ada_parsel', 'tip', 'parsel_alani', 'vasif']], use_container_width=True)

else:
    secilen = st.selectbox("Analiz edilecek parseli seçin:", [p['ada_parsel'] for p in parsel_listesi])
    p = next(item for item in parsel_listesi if item["ada_parsel"] == secilen)
    
    # Skor Hesaplama
    raw_score = (int(p['konum_skoru']) * 0.5) + (float(p['kaks']) * 20)
    if "Tarla" in p['tip']: raw_score -= 30
    score = max(5, min(98, raw_score))
    logic = get_investment_logic(p, score)

    # ÜST KARAR KARTI
    st.markdown(f"""
    <div class="decision-card" style="border-color: {logic['color']}; background: {logic['color']}11;">
        <h1 style="color: {logic['color']}; margin:0;">{logic['label']}</h1>
        <p style="font-size: 20px; color: #8b949e; margin-top:10px;">MAPTİS Güven Skoru: <b>%{score:.1f}</b></p>
        <p style="font-size: 16px;"><b>STRATEJİK EMİR:</b> {logic['action']}</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1.2])

    with c1:
        st.subheader("📊 SWOT Analizi")
        st.markdown(f"""
        <div class="swot-box s-box"><b>💪 GÜÇLÜ (STRENGTHS)</b><br>{p['tip']} vasfı, yüksek konum skoru ({p['konum_skoru']}) ve imar potansiyeli.</div>
        <div class="swot-box w-box"><b>⚠️ ZAYIF (WEAKNESSES)</b><br>{p['jeoloji']} zemin yapısı ve yüksek ilk yatırım maliyeti.</div>
        <div class="swot-box o-box"><b>🚀 FIRSAT (OPPORTUNITIES)</b><br>Bölgedeki %{deger_artis} beklenen değer artışı ve kentsel genişleme hattı.</div>
        <div class="swot-box t-box"><b>🧨 TEHDİT (THREATS)</b><br>Artan inşaat maliyetleri (%{maliyet_artis}) ve mevzuat belirsizlikleri.</div>
        """, unsafe_allow_html=True)

    with c2:
        st.subheader("🧠 Yatırım Gerekçeleri")
        col_yes, col_no = st.columns(2)
        with col_yes:
            st.write("✅ **Neden Alınmalı?**")
            for reason in logic['why_yes']:
                st.markdown(f"<div class='reason-chip'>{reason}</div>", unsafe_allow_html=True)
        with col_no:
            st.write("❌ **Riskler Neler?**")
            for reason in logic['why_no']:
                st.markdown(f"<div class='reason-chip'>{reason}</div>", unsafe_allow_html=True)
        
        st.write("---")
        st.subheader("💰 Maliyet & Projeksiyon")
        area = float(p['parsel_alani'])
        arsa_val = (area * float(p['m2_fiyat'])) / 1e6
        yapim_val = (area * float(p['kaks']) * 22000 * (1 + maliyet_artis/100)) / 1e6
        
        f1, f2 = st.columns(2)
        f1.metric("Arsa Bedeli", f"{arsa_val:.2f}M TL")
        f2.metric("Simüle Yapım Maliyeti", f"{yapim_val:.2f}M TL")
        st.metric("5 Yıl Sonraki Tahmini Değer", f"{(arsa_val * (1 + deger_artis/100)**2):.2f}M TL", delta=f"%{deger_artis} Yıllık Büyüme")

    st.write("---")
    st.info(f"🔍 **Saha Notu:** Bu varlık {p['ada_parsel']} ada/parsel numarasında kayıtlıdır. {p['vasif']} niteliğindedir. Stratejik olarak {'sermaye koruma' if score < 60 else 'sermaye büyütme'} odaklıdır.")