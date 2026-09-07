import streamlit as st
import base64
import requests
import json
import time
from PyPDF2 import PdfReader
import io
import os

st.set_page_config(
    page_title="AI Document Analyzer",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for clean mobile UI without sidebar
st.markdown("""
    <style>
    /* Sembunyikan tombol sidebar toggle */
    [data-testid="collapsedControl"] {
        display: none;
    }
    .main {
        padding: 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        font-weight: bold;
        background-color: #10A37F;
        color: white;
    }
    .uploadedFile {
        border: 2px dashed #10A37F;
        border-radius: 10px;
        padding: 10px;
    }
    .stAlert {
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📄 AI Document Analyzer")
st.caption("Powered by OpenAI GPT-4o-mini | Mobile Optimized")

def get_api_key():
    """Mengambil API key dari Streamlit Secrets atau Environment Variable"""
    if "OPENAI_API_KEY" in st.secrets:
        return st.secrets["OPENAI_API_KEY"]
    return os.environ.get("OPENAI_API_KEY")

api_key = get_api_key()

def extract_text_from_pdf(file_bytes):
    """Ekstrak teks dari file PDF"""
    try:
        pdf_reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text if text.strip() else None
    except Exception:
        return None

def analyze_with_openai(api_key, file_bytes, mime_type, file_name, prompt_text):
    """Mengirim konten ke OpenAI GPT-4o-mini API"""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages_content = []
    
    if "image" in mime_type:
        base64_image = base64.b64encode(file_bytes).decode('utf-8')
        messages_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{base64_image}"
            }
        })
        messages_content.append({"type": "text", "text": prompt_text})
    elif "pdf" in mime_type or file_name.endswith(".pdf"):
        extracted_text = extract_text_from_pdf(file_bytes)
        if not extracted_text:
            return "❌ Tidak dapat membaca teks dari PDF. File mungkin berupa hasil scan gambar atau terkunci."
        combined_prompt = f"{prompt_text}\n\n--- Isi Dokumen ({file_name}) ---\n{extracted_text[:12000]}"
        messages_content.append({"type": "text", "text": combined_prompt})
    else:
        try:
            text_content = file_bytes.decode('utf-8')
            combined_prompt = f"{prompt_text}\n\n--- Isi Dokumen ({file_name}) ---\n{text_content[:12000]}"
            messages_content.append({"type": "text", "text": combined_prompt})
        except Exception:
            return "❌ Gagal membaca isi file teks."

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "Anda adalah asisten analisis dokumen profesional. Berikan respon yang akurat, terstruktur, mudah dibaca di layar HP, dan langsung pada poin utama menggunakan format Markdown."
            },
            {
                "role": "user",
                "content": messages_content
            }
        ],
        "temperature": 0.3
    }

    max_retries = 3
    delay = 1
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            elif response.status_code == 429:
                time.sleep(delay)
                delay *= 2
            else:
                return f"❌ Error API ({response.status_code}): {response.json().get('error', {}).get('message', response.text)}"
        except Exception as e:
            if attempt == max_retries - 1:
                return f"❌ Gagal menghubungi OpenAI API: {str(e)}"
            time.sleep(delay)
            delay *= 2

st.subheader("1. Unggah Dokumen")
uploaded_file = st.file_uploader(
    "Pilih file (PDF, TXT, PNG, JPG)", 
    type=["pdf", "txt", "png", "jpg", "jpeg"],
    help="Maksimal rekomendasi 10MB untuk performa HP optimal"
)

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
    custom_prompt = st.text_area("Tuliskan pertanyaan spesifik Anda tentang dokumen ini:", placeholder="Contoh: Apa saja klausul pembatalan dalam dokumen ini?")

st.subheader("3. Jalankan Analisis")

if st.button("🚀 Analisis Dokumen Sekarang"):
    if not api_key:
        st.error("⚠️ API Key tidak ditemukan! Silakan tambahkan `OPENAI_API_KEY` di **Streamlit Cloud Secrets** (Settings -> Secrets).")
    elif uploaded_file is None:
        st.error("⚠️ Silakan unggah file terlebih dahulu!")
    else:
        prompt_map = {
            "📌 Ringkasan Eksekutif & Poin Utama": "Berikan ringkasan eksekutif komprehensif dari dokumen ini. Buatlah daftar 5-7 poin utama yang paling penting.",
            "💡 Analisis Mendalam & Jawaban Kunci": "Lakukan analisis mendalam terhadap isi dokumen ini. Jelaskan konteks, argumen utama, serta kesimpulan penting yang disampaikan.",
            "📋 Ekstraksi Action Items / Tugas": "Ekstrak semua tindakan/langkah kerja (action items), rekomendasi, atau tugas yang disebutkan dalam dokumen ini dalam bentuk checklist."
        }
        
        final_prompt = custom_prompt if analysis_mode == "🔍 Tanya Jawab Kustom (Custom Prompt)" else prompt_map[analysis_mode]

        file_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type or "application/octet-stream"

        with st.spinner("⏳ Memproses & Menganalisis dokumen via OpenAI GPT-4o-mini..."):
            result_text = analyze_with_openai(api_key, file_bytes, mime_type, uploaded_file.name, final_prompt)

        st.subheader("📊 Hasil Analisis")
        st.markdown(result_text)
        
        st.download_button(
            label="📥 Unduh Hasil Analisis (.txt)",
            data=result_text,
            file_name=f"Analisis_{uploaded_file.name}.txt",
            mime="text/plain"
        )

st.markdown("---")
st.caption("Tips HP Android: Pastikan `OPENAI_API_KEY` sudah terpasang di Secrets aplikasi ini.")
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "Anda adalah asisten analisis dokumen profesional. Berikan respon yang akurat, terstruktur, mudah dibaca di layar HP, dan langsung pada poin utama menggunakan format Markdown."
            },
            {
                "role": "user",
                "content": messages_content
            }
        ],
        "temperature": 0.3
    }

    max_retries = 3
    delay = 1
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            elif response.status_code == 429:
                time.sleep(delay)
                delay *= 2
            else:
                return f"❌ Error API ({response.status_code}): {response.json().get('error', {}).get('message', response.text)}"
        except Exception as e:
            if attempt == max_retries - 1:
                return f"❌ Gagal menghubungi OpenAI API: {str(e)}"
            time.sleep(delay)
            delay *= 2

st.subheader("1. Unggah Dokumen")
uploaded_file = st.file_uploader(
    "Pilih file (PDF, TXT, PNG, JPG)", 
    type=["pdf", "txt", "png", "jpg", "jpeg"],
    help="Maksimal rekomendasi 10MB untuk performa HP optimal"
)

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
    custom_prompt = st.text_area("Tuliskan pertanyaan spesifik Anda tentang dokumen ini:", placeholder="Contoh: Apa saja klausul pembatalan dalam dokumen ini?")

st.subheader("3. Jalankan Analisis")

if st.button("🚀 Analisis Dokumen Sekarang"):
    if not api_key:
        st.error("⚠️ API Key tidak ditemukan! Silakan tambahkan `OPENAI_API_KEY` di **Streamlit Cloud Secrets** (Settings -> Secrets).")
    elif uploaded_file is None:
        st.error("⚠️ Silakan atur dan **unggah file** terlebih dahulu!")
    else:
        prompt_map = {
            "📌 Ringkasan Eksekutif & Poin Utama": "Berikan ringkasan eksekutif komprehensif dari dokumen ini. Buatlah daftar 5-7 poin utama yang paling penting.",
            "💡 Analisis Mendalam & Jawaban Kunci": "Lakukan analisis mendalam terhadap isi dokumen ini. Jelaskan konteks, argumen utama, serta kesimpulan penting yang disampaikan.",
            "📋 Ekstraksi Action Items / Tugas": "Ekstrak semua tindakan/langkah kerja (action items), rekomendasi, atau tugas yang disebutkan dalam dokumen ini dalam bentuk checklist."
        }
        
        final_prompt = custom_prompt if analysis_mode == "🔍 Tanya Jawab Kustom (Custom Prompt)" else prompt_map[analysis_mode]

        file_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type or "application/octet-stream"

        with st.spinner("⏳ Memproses & Menganalisis dokumen via OpenAI GPT-4o-mini..."):
            result_text = analyze_with_openai(api_key, file_bytes, mime_type, uploaded_file.name, final_prompt)

        st.subheader("📊 Hasil Analisis")
        st.markdown(result_text)
        
        st.download_button(
            label="📥 Unduh Hasil Analisis (.txt)",
            data=result_text,
            file_name=f"Analisis_{uploaded_file.name}.txt",
            mime="text/plain"
        )

st.markdown("---")
st.caption("Tips HP Android: Pastikan `OPENAI_API_KEY` sudah terpasang di Secrets aplikasi ini.")
