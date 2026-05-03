import streamlit as st
import openai
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
    .main-header h1 {
        font-size: 2.5em;
        margin-bottom: 5px;
    }
    .main-header p {
        font-size: 1.1em;
        opacity: 0.8;
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        color: white;
        margin: 5px 0;
    }
    .stat-box h3 {
        margin: 0;
        font-size: 1.8em;
    }
    .stat-box p {
        margin: 0;
        font-size: 0.9em;
        opacity: 0.85;
    }
    .success-box {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
    }
    .info-box {
        background: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
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
# YAN MENÜ (SIDEBAR)
# ==============================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=80)
    st.markdown("## ⚙️ Ayarlar")

    api_key = st.text_input(
        "🔑 OpenAI API Anahtarı",
        type="password",
        help="platform.openai.com adresinden alabilirsiniz"
    )

    st.markdown("---")

    # --- Model Seçimi ---
    model_choice = st.selectbox(
        "🤖 Model",
        ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        index=0,
        help="gpt-4o en iyi sonucu verir"
    )

    # --- İnsancılaştırma Seviyesi ---
    humanize_level = st.slider(
        "👤 İnsancılaştırma Seviyesi",
        min_value=1,
        max_value=5,
        value=3,
        help="1: Az değişiklik, 5: Maksimum yeniden yazım"
    )

    # --- Akademik Alan ---
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

    # --- Yazım Dili ---
    output_lang = st.selectbox(
        "🌍 Çıktı Dili",
        ["Türkçe", "English"],
        index=0
    )

    # --- Temperature ---
    temperature = st.slider(
        "🌡️ Yaratıcılık (Temperature)",
        min_value=0.1,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Düşük = daha tutarlı, Yüksek = daha yaratıcı"
    )

    st.markdown("---")

    # --- Mod Seçimi ---
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
        "<p style='text-align:center; opacity:0.6;'>AkademiEdit v1.0<br>"
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
        4: "Belirgin şekilde yeniden yaz, farklı cümle yapıları ve kelime seçimi kullan.",
        5: "Tamamen yeniden yaz, sanki farklı bir akademisyen yazmış gibi olsun."
    }

    field_context = {
        "Endüstri Mühendisliği": "Endüstri Mühendisliği terminolojisini (üretim planlama, kalite kontrol, lojistik, ergonomi, simülasyon, optimizasyon, SCM, TQM, Six Sigma, JIT, vb.) doğru kullan.",
        "İşletme / MBA": "İşletme ve yönetim bilimi terminolojisini (stratejik yönetim, pazarlama, finans, organizasyon, liderlik, vb.) doğru kullan.",
        "Bilgisayar Mühendisliği": "Bilişim terminolojisini (algoritma, veri yapıları, makine öğrenmesi, yazılım mühendisliği, vb.) doğru kullan.",
        "Makine Mühendisliği": "Makine mühendisliği terminolojisini (termodinamik, akışkanlar mekaniği, malzeme bilimi, vb.) doğru kullan.",
        "Ekonomi": "Ekonomi terminolojisini (mikro/makroekonomi, econometri, fiscal policy, vb.) doğru kullan.",
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
    7. Aşırı düzenli geçiş kelimeleri kullanma (Bunun yanı sıra, Ayrıca, Sonuç olarak gibi sürekli tekrar etme).
    8. Her paragrafın yapısını değiştir ama anlamını koru.
    9. Akademik tonu ve resmi dili koru.
    10. {lang_instruction}
    """

    prompts = {
        "🔄 İnsancıllaştır (AI Dedektör)": f"""
        Sen deneyimli bir akademik editörsün. Aşağıdaki metni, AI dedektörlerinin (GPTZero, Turnitin, ZeroGPT vb.)
        tespit edemeyeceği şekilde insancıllaştır.

        {base_rules}

        EK STRATEJİLER:
        - Metnin "perplexity" (karmaşıklık) değerini artır: daha az tahmin edilebilir kelime sıralamaları kullan.
        - "Burstiness" (değişkenlik) değerini artır: bazı cümleleri kısa tut, bazılarını uzun ve bileşik yap.
        - Kişisel akademik üslup izlenimi ver (örn: "bu çalışmada vurgulanmıştır" yerine "elde edilen bulgular göstermektedir ki").
        - Paragraf geçişlerinde beklenmedik yapılar kullan.
        - Kalıp cümleleri (örn: "Bu çalışmada ... ele alınmıştır") çeşitlendir.

        METİN:
        {text}
        """,

        "✏️ Paraphrase (Yeniden Yaz)": f"""
        Sen akademik bir yazma uzmanısın. Aşağıdaki metni anlamını kaybetmeden tamamen farklı kelimeler ve 
        cümle yapıları kullanarak yeniden yaz.

        {base_rules}

        EK STRATEJİLER:
        - Her cümlede en az 2-3 anahtar kelimeyi eş anlamlılarıyla değiştir.
        - Cümle yapısını değiştir (özne-nesne-yüklem sırasını değiştir).
        - Pasif-aktif çatı geçişleri yap.
        - Aynı fakri farklı bir perspektiften ifade et.

        METİN:
        {text}
        """,

        "📖 Akademik Düzeltme": f"""
        Sen kıdemli bir akademik hakem ve editörsün. Aşağıdaki metni akademik yazım kurallarına göre düzelt 
        ve iyileştir. Yazım hatalarını, anlatım bozukluklarını ve tutarsızlıkları gider.

        {base_rules}

        EK STRATEJİLER:
        - İmla ve noktalama hatalarını düzelt.
        - Tekrar eden ifadeleri kaldır.
        - Akademik olmayan günlük dili akademik dile çevir.
        - Paragraf akışını ve mantıksal bütünlüğü güçlendir.
        - Gereksiz süslemeleri kaldır, sade ve net bir dil kullan.

        METİN:
        {text}
        """,

        "📝 Genişlet (Detay Ekle)": f"""
        Sen konusunda uzman bir akademisyensin ({field}). Aşağıdaki metni genişlet ve detaylandır.
        Eksik gördüğün noktalara açıklama ekle, örnekler ver ve analizi derinleştir.

        {base_rules}

        EK STRATEJİLER:
        - Mevcut argümanları destekleyici açıklamalar ekle.
        - Yöntem kısımlarında daha fazla teknik detay ver.
        - Literatür taraması kısımlarına ek bağlam ekle.
        - Sonuç kısımlarına daha geniş çıkarımlar ekle.
        - Uzunluğu en az %30-50 artır.

        METİN:
        {text}
        """,

        "✂️ Kısalt (Özetle)": f"""
        Sen deneyimli bir akademik editörsün. Aşağıdaki metni kısalt ama ana argümanları ve 
        önemli detayları koru. Gereksiz tekrarları ve dolaylı ifadeleri çıkar.

        {base_rules}

        EK STRATEJİLER:
        - Gereksiz tekrarları kaldır.
        - Dolaylı ifadeleri doğrudan yap.
        - Ana argümanları koru ama süsleyici cümleleri çıkar.
        - Uzunluğu en az %30-40 azalt.
        - "Özet olarak" veya "kısacası" gibi geçişler kullanmadan doğrudan ifade et.

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

# İki sütunlu layout
col_input, col_output = st.columns(2)

with col_input:
    st.markdown("### 📥 Girdi Metni")

    input_text = st.text_area(
        "Düzenlenecek metni buraya yapıştırın:",
        height=400,
        placeholder="Örn: Bu çalışmada, üretim hattındaki darboğazların belirlenmesi "
                     "amacıyla simülasyon tabanlı bir yöntem önerilmiştir. "
                     "Veri toplama süreci 6 ay sürmüş olup..."
    )

    # Girdi istatistikleri
    if input_text:
        w, c, s, p = get_text_stats(input_text)
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            st.markdown(f'<div class="stat-box"><h3>{w}</h3><p>Kelime</p></div>',
                        unsafe_allow_html=True)
        with col_s2:
            st.markdown(f'<div class="stat-box"><h3>{c}</h3><p>Karakter</p></div>',
                        unsafe_allow_html=True)
        with col_s3:
            st.markdown(f'<div class="stat-box"><h3>{s}</h3><p>Cümle</p></div>',
                        unsafe_allow_html=True)
        with col_s4:
            st.markdown(f'<div class="stat-box"><h3>{p}</h3><p>Paragraf</p></div>',
                        unsafe_allow_html=True)

with col_output:
    st.markdown("### 📤 Düzenlenmiş Metn")

    # Sonuç alanı (session state ile)
    if 'output_text' not in st.session_state:
        st.session_state.output_text = ""

    output_placeholder = st.empty()

    if st.session_state.output_text:
        output_placeholder.text_area(
            "Sonuç:",
            value=st.session_state.output_text,
            height=400,
            key="output_display"
        )
    else:
        output_placeholder.text_area(
            "Sonuç:",
            value="",
            height=400,
            placeholder="Düzenlenmiş metin burada görünecek...",
            key="output_empty"
        )

    # Çıktı istatistikleri
    if st.session_state.output_text:
        w2, c2, s2, p2 = get_text_stats(st.session_state.output_text)
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            st.markdown(f'<div class="stat-box"><h3>{w2}</h3><p>Kelime</p></div>',
                        unsafe_allow_html=True)
        with col_s2:
            st.markdown(f'<div class="stat-box"><h3>{c2}</h3><p>Karakter</p></div>',
                        unsafe_allow_html=True)
        with col_s3:
            st.markdown(f'<div class="stat-box"><h3>{s2}</h3><p>Cümle</p></div>',
                        unsafe_allow_html=True)
        with col_s4:
            st.markdown(f'<div class="stat-box"><h3>{p2}</h3><p>Paragraf</p></div>',
                        unsafe_allow_html=True)


# ==============================
# BUTONLAR
# ==============================
st.markdown("---")
col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)

with col_btn1:
    run_button = st.button("🚀 Metni Düzenle", type="primary", use_container_width=True)

with col_btn2:
    clear_button = st.button("🗑️ Temizle", use_container_width=True)

with col_btn3:
    copy_button = st.button("📋 Kopyala", use_container_width=True,
                            help="Sonucu panoya kopyalar")

with col_btn4:
    download_button = st.download_button(
        "💾 İndir (.txt)",
        data=st.session_state.output_text if st.session_state.output_text else "",
        file_name=f"duzenlenmis_metin_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain",
        use_container_width=True,
        disabled=not bool(st.session_state.output_text)
    )


# ==============================
# İŞLEM MANTIĞI
# ==============================
if clear_button:
    st.session_state.output_text = ""
    st.rerun()

if copy_button and st.session_state.output_text:
    st.code(st.session_state.output_text, language=None)
    st.info("📋 Metin yukarıda görüntüleniyor. Manuel olarak kopyalayabilirsiniz.")

if run_button:
    # Kontroller
    if not api_key:
        st.error("⚠️ Lütfen sol menüden OpenAI API anahtarınızı girin!")
        st.info("💡 [platform.openai.com](https://platform.openai.com) adresinden "
                "API anahtarı alabilirsiniz.")
    elif not input_text.strip():
        st.error("⚠️ Lütfen düzenlenecek bir metin girin!")
    elif len(input_text.strip()) < 50:
        st.warning("⚠️ Metin çok kısa. En az 50 karakter girin.")
    else:
        # API çağrısı
        client = openai.OpenAI(api_key=api_key)
        prompt = get_prompt(mode, input_text, humanize_level, academic_field, output_lang)

        try:
            with st.spinner(f"🔄 {mode} uygulanıyor... Lütfen bekleyin."):
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.02)
                    progress_bar.progress(i + 1)

                response = client.chat.completions.create(
                    model=model_choice,
                    messages=[
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
                    temperature=temperature,
                    max_tokens=4096
                )

                result = response.choices[0].message.content
                st.session_state.output_text = result
                progress_bar.progress(100)

            st.success("✅ Düzenleme tamamlandı!")
            st.rerun()

        except openai.AuthenticationError:
            st.error("❌ API anahtarı geçersiz. Lütfen kontrol edin.")
        except openai.RateLimitError:
            st.error("❌ API kota sınırına ulaşıldı. Lütfen biraz bekleyin.")
        except openai.APIError as e:
            st.error(f"❌ API Hatası: {str(e)}")
        except Exception as e:
            st.error(f"❌ Beklenmeyen hata: {str(e)}")


# ==============================
# ALT BİLGİ PANELİ
# ==============================
st.markdown("---")

with st.expander("💡 Kullanım İpuçları", expanded=False):
    st.markdown("""
    ### 🎯 AI Dedektörlerinden Geçmek İçin İpuçları

    | Strateji | Açıklama |
    |----------|----------|
    | **Perplexity Artırma** | Tahmin edilemez kelime sıralamaları kullanın |
    | **Burstiness** | Cümle uzunluklarını çeşitlendirin |
    | **Aktif/Pasif Karışımı** | Sadece edilgen çatı kullanmayın |
    | **Özgün Terminoloji** | Alanınıza özgü spesifik terimler kullanın |
    | **Kişisel Üslup** | Her paragrafta farklı anlatım tekniği deneyin |

    ### 📊 En İyi Sonuç İçin
    - **İnsancılaştırma seviyesi 3-4** idealdir
    - **Temperature 0.6-0.8** en dengeli sonucu verir
    - **gpt-4o** modeli en insansı metni üretir
    - Metni **paragraf paragraf** düzenleyin (500+ kelimeyi tek seferde göndermeyin)
    """)

with st.expander("🔬 AI Dedektör Testleri", expanded=False):
    st.markdown("""
    ### 🌐 Ücretsiz AI Dedektörleri
    Düzenlediğiniz metni şu sitelerde test edebilirsiniz:

    1. **[GPTZero](https://gptzero.me)** - En popüler
    2. **[ZeroGPT](https://zerogpt.com)** - Hızlı ve ücretsiz
    3. **[Copyleaks](https://copyleaks.com/ai-content-detector)** - Doğruluk oranı yüksek
    4. **[Sapling](https://sapling.ai/ai-content-detector)** - Detaylı analiz
    5. **[Writer.com](https://writer.com/ai-content-detector)** - Basit arayüz

    ### 📈 Geçme Oranı Artırma Tüyoları
    - Düzenlenen metni bir kez daha **"İnsancıllaştır"** modundan geçirin
    - Farklı **temperature** değerleri deneyin
    - Çok uzun metinleri **bölerek** gönderin
    """)

with st.expander("⚠️ Akademik Etik Uyarısı", expanded=True):
    st.markdown("""
    ### 📜 Önemli Bilgilendirme

    Bu araç, **akademik yazımınızı iyileştirmek** amacıyla tasarlanmıştır.

    - ✅ **Doğru kullanım:** Anlatım bozukluklarını giderme, dil düzeltme, ifade iyileştirme
    - ❌ **Yanlış kullanım:** Sıfırdan metin üretme, başkasının çalışmasını kendi gibi gösterme

    > 🔬 Tezin özgün katkısı **sizin analizleriniz, modelleriniz ve bulgularınızdır.**
    > Bu araç sadece **dil ve anlatım** kalitesini artırmak için kullanılmalıdır.
    """)

# Footer
st.markdown("""
<div style="text-align:center; padding:20px; opacity:0.5;">
    <p>AkademiEdit v1.0 | MiMo tarafından geliştirilmiştir | 2025</p>
</div>
""", unsafe_allow_html=True)
