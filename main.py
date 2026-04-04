import json

# MAPTIS Çekirdek Algoritması v0.1
def maptis_analiz(veri):
    # Kapasite ve Risk Hesaplama
    insaat_alani = veri['parsel_alani'] * veri['kaks']
    risk_puanı = 100 - (veri['kat_adedi'] * 2) + (veri['konum_skoru'] * 0.1)
    return round(insaat_alani, 2), round(risk_puanı, 2)

# Veriyi oku
with open('data_input.json', 'r', encoding='utf-8') as f:
    parsel_verisi = json.load(f)

alan, risk = maptis_analiz(parsel_verisi)

print("-" * 40)
print(f"MAPTİS YATIRIM ANALİZİ: {parsel_verisi['ada_parsel']}")
print(f"Maksimum İnşaat Alanı: {alan} m2")
print(f"Kompozit Risk Skoru: {risk}/100")
print("-" * 40)