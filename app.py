import streamlit as st
import requests
import time
import re
from datetime import datetime

# ==============================
# SAYFA AYARLARI
# ==============================
st.set_page_config(
    page_title="AkademiEdit - Tez Düzenleyici",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# CSS STİLLERİ
# ==============================
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 20px 0;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 15px;
        margin-bottom: 30px;
        color: white;
    }
    .main-header h1 { font-size: 2.5em; margin-bottom: 5px; }
    .main-header p { font-size: 1.1em; opacity: 0.8; }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        color: white;
        margin: 5px 0;
    }
    .stat-box h3 { margin: 0; font-size: 1.8em; }
    .stat-box p { margin: 0; font-size: 0.9em; opacity: 0.85; }
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        font-size: 1.1em;
        padding: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==============================
# BAŞLIK
# ==============================
st.markdown("""
<div class="main-header">
    <h1>🎓 AkademiEdit</h1>
    <p>Endüstri Mühendisliği Tez Düzenleyici & AI İnsancıllaştırıcı</p>
</div>
""", unsafe_allow_html=True)

# ==============================
# GROQ API FONKSİYONU (ÜCRETSİZ)
# ==============================
def call_groq(api_key, prompt, model="llama-3.3-70b-versatile"):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Sen Türk akademik camiasında tanınmış, deneyimli bir "
                    "akademik editör ve dil uzmanısın. Endüstri Mühendisliği "
                    "alanında yayınlanmış makalelerin var. Metinleri AI "
                    "dedektörlerinden geçecek şekilde insancıllaştırma "
                    "konusunda uzmansın."
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4096
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"API Hatası ({response.status_code}): {response.text}")

# ==============================
# YAN MENÜ
# ==============================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=80)
    st.markdown("## ⚙️ Ayarlar")

    api_key = st.text_input(
        "🔑 Groq API Anahtarı",
        type="password",
        help="console.groq.com adresinden ÜCRETSİZ alabilirsiniz"
    )

    st.markdown("### 🆓 Ücretsiz API Nasıl Alınır?")
    st.markdown("""
    1. [console.groq.com](https://console.groq.com) adresine git
    2. Google ile giriş yap
    3. **"API Keys"** → **"Create API Key"**
    4. Oluşan anahtarı buraya yapıştır
    """)

    st.markdown("---")

    model_choice = st.selectbox(
        "🤖 Model",
        [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ],
        index=0,
        help="llama-3.3-70b en iyi Türkçe sonuç verir"
    )

    st.markdown("---")

    humanize_level = st.slider(
        "👤 İnsancılaştırma Seviyesi",
        min_value=1, max_value=5, value=3
    )

    academic_field = st.selectbox(
        "📚 Akademik Alan",
        [
            "Endüstri Mühendisliği",
            "İşletme / MBA",
            "Bilgisayar Mühendisliği",
            "Makine Mühendisliği",
            "Ekonomi",
            "Genel Akademik"
        ],
        index=0
    )

    output_lang = st.selectbox(
        "🌍 Çıktı Dili",
        ["Türkçe", "English"],
        index=0
    )

    temperature = st.slider(
        "🌡️ Yaratıcılık (Temperature)",
        min_value=0.1, max_value=1.0, value=0.7, step=0.1
    )

    st.markdown("---")

    mode = st.radio(
        "📝 İşlem Modu",
        [
            "🔄 İnsancıllaştır (AI Dedektör)",
            "✏️ Paraphrase (Yeniden Yaz)",
            "📖 Akademik Düzeltme",
            "📝 Genişlet (Detay Ekle)",
            "✂️ Kısalt (Özetle)"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown(
        "<p style='text-align:center; opacity:0.6;'>AkademiEdit v2.0<br>"
        "Groq + Llama ile çalışır<br>"
        "MiMo tarafından oluşturuldu</p>",
        unsafe_allow_html=True
    )

# ==============================
# PROMPT ŞABLONLARI
# ==============================
def get_prompt(mode, text, level, field, lang):
    level_descriptions = {
        1: "Çok hafif düzeltmeler yap, çoğu cümleyi olduğu gibi bırak.",
        2: "Hafif yeniden yapılandırma yap, ana yapıyı koru.",
        3: "Orta düzeyde yeniden yaz, anlamı koru ama ifadeleri değiştir.",
        4: "Belirgin şekilde yeniden yaz, farklı cümle yapıları kullan.",
        5: "Tamamen yeniden yaz, sanki farklı bir akademisyen yazmış gibi olsun."
    }

    field_context = {
        "Endüstri Mühendisliği": "Endüstri Mühendisliği terminolojisini (üretim planlama, kalite kontrol, lojistik, ergonomi, simülasyon, optimizasyon, SCM, TQM, Six Sigma, JIT) doğru kullan.",
        "İşletme / MBA": "İşletme terminolojisini (stratejik yönetim, pazarlama, finans, organizasyon) doğru kullan.",
        "Bilgisayar Mühendisliği": "Bilişim terminolojisini (algoritma, veri yapıları, makine öğrenmesi) doğru kullan.",
        "Makine Mühendisliği": "Makine mühendisliği terminolojisini (termodinamik, malzeme bilimi) doğru kullan.",
        "Ekonomi": "Ekonomi terminolojisini (mikro/makroekonomi, ekonometri) doğru kullan.",
        "Genel Akademik": "Genel akademik yazım kurallarına uy."
    }

    lang_instruction = "Yanıtı Türkçe olarak ver." if lang == "Türkçe" else "Respond in English."

    base_rules = f"""
    KURALLAR:
    1. {level_descriptions[level]}
    2. {field_context[field]}
    3. Cümle uzunluklarını çeşitlendir (kısa-uzun-bileşik karışık kullan).
    4. Parantez içi açıklamaları ve teknik terimleri koru.
    5. Sayısal değerleri, formülleri ve tablo/rakam referanslarını AYNEN koru.
    6. Atıf formatlarını (Yazar, Yıl) koruma.
    7. Aşırı düzenli geçiş kelimeleri kullanma.
    8. Her paragrafın yapısını değiştir ama anlamını koru.
    9. Akademik tonu ve resmi dili koru.
    10. {lang_instruction}
    11. SADECE düzenlenmiş metni ver. Açıklama, başlık veya not ekleme.
    """

    prompts = {
        "🔄 İnsancıllaştır (AI Dedektör)": f"""
        Sen deneyimli bir akademik editörsün. Aşağıdaki metni, AI dedektörlerinin
        (GPTZero, Turnitin, ZeroGPT) tespit edemeyeceği şekilde insancıllaştır.

        {base_rules}

        EK STRATEJİLER:
        - "Perplexity" artır: daha az tahmin edilebilir kelime sıralamaları kullan.
        - "Burstiness" artır: bazı cümleleri kısa tut, bazılarını uzun yap.
        - Kişisel akademik üslup izlenimi ver.
        - Kalıp cümleleri çeşitlendir.
        - Her paragrafta farklı anlatım tekniği kullan.

        METİN:
        {text}
        """,

        "✏️ Paraphrase (Yeniden Yaz)": f"""
        Sen akademik bir yazma uzmanısın. Aşağıdaki metni anlamını kaybetmeden
        tamamen farklı kelimeler ve cümle yapıları kullanarak yeniden yaz.

        {base_rules}

        EK STRATEJİLER:
        - Her cümlede en az 2-3 anahtar kelimeyi eş anlamlılarıyla değiştir.
        - Cümle yapısını değiştir (özne-nesne-yüklem sırasını değiştir).
        - Pasif-aktif çatı geçişleri yap.
        - Aynı fikri farklı perspektiften ifade et.

        METİN:
        {text}
        """,

        "📖 Akademik Düzeltme": f"""
        Sen kıdemli bir akademik hakem ve editörsün. Aşağıdaki metni akademik
        yazım kurallarına göre düzelt ve iyileştir.

        {base_rules}

        EK STRATEJİLER:
        - İmla ve noktalama hatalarını düzelt.
        - Tekrar eden ifadeleri kaldır.
        - Günlük dili akademik dile çevir.
        - Paragraf akışını güçlendir.

        METİN:
        {text}
        """,

        "📝 Genişlet (Detay Ekle)": f"""
        Sen konusunda uzman bir akademisyensin ({field}). Aşağıdaki metni
        genişlet ve detaylandır.

        {base_rules}

        EK STRATEJİLER:
        - Destekleyici açıklamalar ekle.
        - Yöntem kısımlarında teknik detay ver.
        - Uzunluğu en az %30-50 artır.

        METİN:
        {text}
        """,

        "✂️ Kısalt (Özetle)": f"""
        Sen deneyimli bir akademik editörsün. Aşağıdaki metni kısalt ama
        ana argümanları koru.

        {base_rules}

        EK STRATEJİLER:
        - Gereksiz tekrarları kaldır.
        - Dolaylı ifadeleri doğrudan yap.
        - Uzunluğu en az %30-40 azalt.

        METİN:
        {text}
        """
    }

    return prompts.get(mode, prompts["🔄 İnsancıllaştır (AI Dedektör)"])

# ==============================
# İSTATİSTİKLER
# ==============================
def get_text_stats(text):
    if not text.strip():
        return 0, 0, 0, 0
    words = len(text.split())
    chars = len(text)
    sentences = len(re.split(r'[.!?]+', text.strip())) - 1
    paragraphs = len([p for p in text.split('\n\n') if p.strip()])
    return words, chars, sentences, paragraphs

# ==============================
# ANA İÇERİK
# ==============================
col_input, col_output = st.columns(2)

with col_input:
    st.markdown("### 📥 Girdi Metni")

    input_text = st.text_area(
        "Düzenlenecek metni buraya yapıştırın:",
        height=400,
        placeholder="Örn: Bu çalışmada, üretim hattındaki darboğazların "
                     "belirlenmesi amacıyla simülasyon tabanlı bir yöntem "
                     "önerilmiştir..."
    )

    if input_text:
        w, c, s, p = get_text_stats(input_text)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="stat-box"><h3>{w}</h3><p>Kelime</p></div>',
                        unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="stat-box"><h3>{c}</h3><p>Karakter</p></div>',
                        unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="stat-box"><h3>{s}</h3><p>Cümle</p></div>',
                        unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="stat-box"><h3>{p}</h3><p>Paragraf</p></div>',
                        unsafe_allow_html=True)

with col_output:
    st.markdown("### 📤 Düzenlenmiş Metin")

    if 'output_text' not in st.session_state:
        st.session_state.output_text = ""

    if st.session_state.output_text:
        st.text_area(
            "Sonuç:",
            value=st.session_state.output_text,
            height=400,
            key="output_display"
        )
    else:
        st.text_area(
            "Sonuç:",
            value="",
            height=400,
            placeholder="Düzenlenmiş metin burada görünecek...",
            key="output_empty"
        )

    if st.session_state.output_text:
        w2, c2, s2, p2 = get_text_stats(st.session_state.output_text)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="stat-box"><h3>{w2}</h3><p>Kelime</p></div>',
                        unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="stat-box"><h3>{c2}</h3><p>Karakter</p></div>',
                        unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="stat-box"><h3>{s2}</h3><p>Cümle</p></div>',
                        unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="stat-box"><h3>{p2}</h3><p>Paragraf</p></div>',
                        unsafe_allow_html=True)

# ==============================
# BUTONLAR
# ==============================
st.markdown("---")
col_b1, col_b2, col_b3, col_b4 = st.columns(4)

with col_b1:
    run_button = st.button("🚀 Metni Düzenle", type="primary",
                           use_container_width=True)
with col_b2:
    clear_button = st.button("🗑️ Temizle", use_container_width=True)
with col_b3:
    pass
with col_b4:
    download_button = st.download_button(
        "💾 İndir (.txt)",
        data=st.session_state.output_text if st.session_state.output_text else "",
        file_name=f"duzenlenmis_metin_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain",
        use_container_width=True,
        disabled=not bool(st.session_state.output_text)
    )

# ==============================
# İŞLEM
# ==============================
if clear_button:
    st.session_state.output_text = ""
    st.rerun()

if run_button:
    if not api_key:
        st.error("⚠️ Lütfen sol menüden Groq API anahtarınızı girin!")
        st.info("🆓 [console.groq.com](https://console.groq.com) adresinden "
                "ücretsiz API anahtarı alabilirsiniz.")
    elif not input_text.strip():
        st.error("⚠️ Lütfen düzenlenecek bir metin girin!")
    elif len(input_text.strip()) < 30:
        st.warning("⚠️ Metin çok kısa. En az 30 karakter girin.")
    else:
        prompt = get_prompt(mode, input_text, humanize_level,
                           academic_field, output_lang)
        try:
            with st.spinner(f"🔄 {mode} uygulanıyor... Lütfen bekleyin."):
                progress_bar = st.progress(0)
                for i in range(50):
                    time.sleep(0.02)
                    progress_bar.progress(i + 1)

                result = call_groq(api_key, prompt, model_choice)

                for i in range(50, 100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)

                st.session_state.output_text = result
                progress_bar.progress(100)

            st.success("✅ Düzenleme tamamlandı!")
            st.rerun()

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "invalid" in error_msg.lower():
                st.error("❌ API anahtarı geçersiz. Groq console'dan yeni anahtar alın.")
            elif "429" in error_msg or "rate" in error_msg.lower():
                st.error("❌ Çok hızlı istek gönderdiniz. 1 dakika bekleyin.")
            else:
                st.error(f"❌ Hata: {error_msg}")

# ==============================
# BİLGİ PANELLERİ
# ==============================
st.markdown("---")

with st.expander("🆓 Groq API Ücretsiz Mi?", expanded=True):
    st.markdown("""
    ### ✅ Evet, tamamen ücretsiz!

    | Özellik | Detay |
    |---------|-------|
    | **Fiyat** | $0 (ücretsiz) |
    | **Hız** | Saniyede 100+ token (OpenAI'den 10x hızlı) |
    | **Limit** | Dakikada ~30 istek |
    | **Modeller** | Llama 3.3 70B, Mixtral, Gemma |
    | **Kalite** | GPT-4 seviyesinde Türkçe performans |

    ### 🔑 API Anahtarı Alma Adımları

    1. **[console.groq.com](https://console.groq.com)** adresine git
    2. **"Sign up"** → Google hesabınla giriş yap
    3. Sol menüden **"API Keys"** tıkla
    4. **"Create API Key"** → İsim ver (örn: "tez")
    5. Oluşan anahtarı kopyala → buraya yapıştır

    > ⚠️ Anahtar bir kez gösterilir, kaybetmemek için bir yere not et!
    """)

with st.expander("🎯 En İyi Sonuç İçin İpuçları", expanded=False):
    st.markdown("""
    | İpucu | Açıklama |
|-------|----------|
| **Paragraf paragraf gönder** | 500+ kelimeyi tek seferde değil, bölüm bölüm yapıştır |
| **Seviye 3-4 kullan** | En dengeli sonuç |
| **Temperature 0.6-0.8** | Hem yaratıcı hem tutarlı |
| **llama-3.3-70b** | En iyi Türkçe model |
| **2 kez üst üste çalıştır** | İkinci geçiş daha insansı yapar |
    """)

with st.expander("🔬 AI Dedektör Test Siteleri", expanded=False):
    st.markdown("""
    Düzenlediğiniz metni test edin:

    1. **[GPTZero](https://gptzero.me)**
    2. **[ZeroGPT](https://zerogpt.com)**
    3. **[Copyleaks](https://copyleaks.com/ai-content-detector)**
    4. **[Sapling](https://sapling.ai/ai-content-detector)**
    """)

st.markdown("""
<div style="text-align:center; padding:20px; opacity:0.5;">
    <p>AkademiEdit v2.0 | Groq + Llama 3.3 | MiMo tarafından geliştirilmiştir | 2025</p>
</div>
""", unsafe_allow_html=True)
