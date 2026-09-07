import streamlit as st
import base64
import requests
import json
import time

st.set_page_config(
    page_title="AI Document Analyzer",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for clean mobile UI and dark mode compatibility
st.markdown("""
    <style>
    .main {
        padding: 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        font-weight: bold;
        background-color: #4F46E5;
        color: white;
    }
    .uploadedFile {
        border: 2px dashed #4F46E5;
        border-radius: 10px;
        padding: 10px;
    }
    .stAlert {
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📄 AI Document Analyzer")
st.caption("Powered by Gemini 3 Flash | Mobile Optimized")

# Sidebar for API Key input
with st.sidebar:
    st.header("⚙️ Konfigurasi")
    api_key_input = st.text_input("Gemini API Key", type="password", help="Masukkan API Key Gemini Anda")
    st.info("API Key bisa didapatkan gratis di Google AI Studio.")

def analyze_document_with_gemini(api_key, file_bytes, mime_type, prompt_text):
    """
    Mengirimkan dokumen langsung dalam format Base64 ke Gemini 3 Flash API.
    Metode ini sangat ringan dan tidak membuat server/HP crash.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={api_key}"
    
    # Encode bytes to Base64
    base64_data = base64.b64encode(file_bytes).decode('utf-8')
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": base64_data
                        }
                    },
                    {
                        "text": prompt_text
                    }
                ]
            }
        ],
        "systemInstruction": {
            "parts": [
                {
                    "text": "Anda adalah asisten analisis dokumen profesional. Berikan respon yang akurat, terstruktur, mudah dibaca di layar HP, dan langsung pada poin utama menggunakan format Markdown."
                }
            ]
        }
    }

    headers = {'Content-Type': 'application/json'}
    
    # Exponential backoff implementation for API retries
    max_retries = 3
    delay = 1
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                try:
                    return result['candidates'][0]['content']['parts'][0]['text']
                except (KeyError, IndexError):
                    return "❌ Gagal mengekstrak respon dari model. Format output tidak sesuai."
            elif response.status_code == 429:
                time.sleep(delay)
                delay *= 2
            else:
                return f"❌ Error API ({response.status_code}): {response.text}"
        except Exception as e:
            if attempt == max_retries - 1:
                return f"❌ Gagal menghubungi API: {str(e)}"
            time.sleep(delay)
            delay *= 2

st.subheader("1. Unggah Dokumen")
uploaded_file = st.file_uploader(
    "Pilih file (PDF, TXT, PNG, JPG)", 
    type=["pdf", "txt", "png", "jpg", "jpeg"],
    help="Maksimal rekomendasi 10MB untuk performa HP optimal"
)

# File status and details
if uploaded_file is not None:
    file_size_mb = uploaded_file.size / (1024 * 1024)
    st.success(f"📎 **{uploaded_file.name}** ({file_size_mb:.2f} MB)")
    
    if file_size_mb > 15:
        st.warning("⚠️ Ukuran file cukup besar, proses analisis mungkin membutuhkan waktu lebih lama di HP.")

st.subheader("2. Pilih Mode Analisis")

analysis_mode = st.selectbox(
    "Ingin analisis seperti apa?",
    [
        "📌 Ringkasan Eksekutif & Poin Utama",
        "💡 Analisis Mendalam & Jawaban Kunci",
        "📋 Ekstraksi Action Items / Tugas",
        "🔍 Tanya Jawab Kustom (Custom Prompt)"
    ]
)

custom_prompt = ""
if analysis_mode == "🔍 Tanya Jawab Kustom (Custom Prompt)":
    custom_prompt = st.text_area("Tuliskan pertanyaan spesifik Anda tentang dokumen ini:", placeholder="Contoh: Apa saja klausul pembatalan dalam kontrak ini?")

st.subheader("3. Jalankan Analisis")

if st.button("🚀 Analisis Dokumen Sekarang"):
    if not api_key_input:
        st.error("⚠️ Silakan masukkan **Gemini API Key** di menu sidebar samping kiri terlebih dahulu!")
    elif uploaded_file is None:
        st.error("⚠️ Silakan atur dan **unggah file** terlebih dahulu!")
    else:
        # Determine prompt based on selected mode
        prompt_map = {
            "📌 Ringkasan Eksekutif & Poin Utama": "Berikan ringkasan eksekutif komprehensif dari dokumen ini. Buatlah daftar 5-7 poin utama yang paling penting.",
            "💡 Analisis Mendalam & Jawaban Kunci": "Lakukan analisis mendalam terhadap isi dokumen ini. Jelaskan konteks, argumen utama, serta kesimpulan penting yang disampaikan.",
            "📋 Ekstraksi Action Items / Tugas": "Ekstrak semua tindakan/langkah kerja (action items), rekomendasi, atau tugas yang disebutkan dalam dokumen ini dalam bentuk checklist."
        }
        
        final_prompt = custom_prompt if analysis_mode == "🔍 Tanya Jawab Kustom (Custom Prompt)" else prompt_map[analysis_mode]

        # Read file bytes directly
        file_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type
        
        # Fallback for plain text mime type if missing
        if not mime_type:
            if uploaded_file.name.endswith(".pdf"):
                mime_type = "application/pdf"
            elif uploaded_file.name.endswith(".txt"):
                mime_type = "text/plain"
            elif uploaded_file.name.endswith((".png", ".jpg", ".jpeg")):
                mime_type = f"image/{uploaded_file.name.split('.')[-1]}"

        with st.spinner("⏳ Memproses & Menganalisis dokumen langsung via Gemini AI..."):
            result_text = analyze_document_with_gemini(api_key_input, file_bytes, mime_type, final_prompt)

        st.subheader("📊 Hasil Analisis")
        st.markdown(result_text)
        
        # Option to download result as TXT
        st.download_button(
            label="📥 Unduh Hasil Analisis (.txt)",
            data=result_text,
            file_name=f"Analisis_{uploaded_file.name}.txt",
            mime="text/plain"
        )

st.markdown("---")
st.caption("Tips HP Android: Jika aplikasi sering restart, buat file `.streamlit/config.toml` di repo GitHub kamu dengan opsi `maxUploadSize = 200`.")
