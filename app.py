import streamlit as st
import base64
import requests
import time
from PyPDF2 import PdfReader
import io

st.set_page_config(
    page_title="AI Document Analyzer",
    page_icon="📄",
    layout="centered"
)

# ===== CSS =====
st.markdown("""
<style>

[data-testid="collapsedControl"]{
    display:none;
}

section[data-testid="stSidebar"]{
    display:none;
}

header{
    visibility:hidden;
}

footer{
    visibility:hidden;
}

.main{
    padding-top:1rem;
    padding-bottom:1rem;
}

.stButton>button{
    width:100%;
    border-radius:12px;
    height:48px;
    font-weight:600;
}

</style>
""", unsafe_allow_html=True)

st.title("📄 AI Document Analyzer")
st.caption("Analisis dokumen berbasis AI")

# ===================================================
# API KEY
# ===================================================

def get_api_key():
    return st.secrets.get("OPENAI_API_KEY", "")

api_key = get_api_key()

# ===================================================
# PDF READER
# ===================================================

def extract_text_from_pdf(file_bytes):

    try:

        reader = PdfReader(io.BytesIO(file_bytes))

        text = ""

        for page in reader.pages:

            content = page.extract_text()

            if content:
                text += content + "\n"

        if text.strip():
            return text

        return None

    except Exception:
        return None

# ===================================================
# OPENAI REQUEST
# ===================================================

def analyze_with_openai(
    api_key,
    file_bytes,
    mime_type,
    file_name,
    prompt_text
):

    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages_content = []

    # IMAGE
    if "image" in mime_type:

        image64 = base64.b64encode(file_bytes).decode("utf-8")

        messages_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{image64}"
            }
        })

        messages_content.append({
            "type": "text",
            "text": prompt_text
        })

    # PDF
    elif "pdf" in mime_type or file_name.lower().endswith(".pdf"):

        extracted_text = extract_text_from_pdf(file_bytes)

        if not extracted_text:
            return "Dokumen PDF tidak dapat dibaca."

        combined_prompt = (
            f"{prompt_text}\n\n"
            f"--- {file_name} ---\n"
            f"{extracted_text[:12000]}"
        )

        messages_content.append({
            "type":"text",
            "text":combined_prompt
        })
            # TEXT
    else:

        try:

            text_content = file_bytes.decode("utf-8")

        except UnicodeDecodeError:

            return "File teks tidak dapat dibaca."

        combined_prompt = (
            f"{prompt_text}\n\n"
            f"--- {file_name} ---\n"
            f"{text_content[:12000]}"
        )

        messages_content.append({
            "type": "text",
            "text": combined_prompt
        })

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Anda adalah AI untuk analisis dokumen. "
                    "Berikan jawaban yang ringkas, jelas, terstruktur, "
                    "dan gunakan Markdown."
                )
            },
            {
                "role": "user",
                "content": messages_content
            }
        ],
        "temperature": 0.3
    }

    try:

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=90
        )

        response.raise_for_status()

        result = response.json()

        return result["choices"][0]["message"]["content"]

    except Exception as e:

        return f"❌ Error:\n\n{e}"
        # ===================================================
# USER INTERFACE
# ===================================================

st.subheader("1. Upload Dokumen")

uploaded_file = st.file_uploader(
    "Pilih file",
    type=[
        "pdf",
        "txt",
        "png",
        "jpg",
        "jpeg"
    ]
)

if uploaded_file is not None:

    size_mb = uploaded_file.size / (1024 * 1024)

    st.success(
        f"📎 {uploaded_file.name} ({size_mb:.2f} MB)"
    )


st.subheader("2. Pilih Analisis")

analysis_mode = st.selectbox(
    "Mode Analisis",
    [
        "Ringkasan Eksekutif",
        "Analisis Mendalam",
        "Action Items",
        "Prompt Kustom"
    ]
)

custom_prompt = ""

if analysis_mode == "Prompt Kustom":

    custom_prompt = st.text_area(
        "Masukkan pertanyaan"
    )


st.subheader("3. Analisis")

if st.button("🚀 Analisis Dokumen"):

    if uploaded_file is None:

        st.warning("Silakan upload dokumen terlebih dahulu.")

    elif not api_key:

        st.error("API belum dikonfigurasi.")

    else:

        prompt_map = {

            "Ringkasan Eksekutif":
            "Buat ringkasan eksekutif beserta poin-poin utama.",

            "Analisis Mendalam":
            "Lakukan analisis mendalam terhadap isi dokumen.",

            "Action Items":
            "Ekstrak seluruh action items menjadi checklist."
        }

        if analysis_mode == "Prompt Kustom":

            final_prompt = custom_prompt

        else:

            final_prompt = prompt_map[analysis_mode]

        file_bytes = uploaded_file.getvalue()

        mime_type = uploaded_file.type

        with st.spinner("Sedang menganalisis..."):

            result = analyze_with_openai(
                api_key,
                file_bytes,
                mime_type,
                uploaded_file.name,
                final_prompt
            )

        st.divider()

        st.subheader("Hasil Analisis")

        st.markdown(result)

        st.download_button(
            "📥 Download Hasil",
            data=result,
            file_name="hasil_analisis.txt",
            mime="text/plain"
        )


st.divider()

st.caption("AI Document Analyzer • Powered by OpenAI")
