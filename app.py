import streamlit as st
from io import BytesIO
import traceback

from parser import extract_text
from analyzer import DocumentAnalyzer
from utils import (
    parse_response,
    build_markdown_report,
    item_count
)

st.set_page_config(
    page_title="AI Document Analyzer",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Document Analyzer")

st.write(
    "Upload a PDF atau DOCX untuk generate summary, insights, facts, claims, dan action items."
)

api_key = st.secrets.get("OPENAI_API_KEY", None)
if not api_key:
    st.error("OPENAI_API_KEY not found.")
    st.stop()

# Simple wrapper that mimics the attributes/methods parser expects
class UploadedBytesWrapper:
    def init(self, name: str, data: bytes, mime_type: str = ""):
        self.name = name
        self._data = data
        self.type = mime_type or ""
        self.size = len(data)

    def read(self):
        # return full bytes every time (parser expects bytes)
        return self._data

# File uploader (restrict to pdf/docx)
uploaded = st.file_uploader(
    "Upload Document",
    type=["pdf", "docx"],
    key="document_upload"
)

# If user selected via file_uploader, read once and store bytes in session_state
if uploaded is not None:
    prev_name = st.session_state.get("uploaded_name")
    # only read and store when different file is chosen
    if prev_name != uploaded.name:
        try:
            data = uploaded.read()
            st.session_state["uploaded_bytes"] = data
            st.session_state["uploaded_name"] = uploaded.name
            st.session_state["uploaded_type"] = uploaded.type
            st.success(f"File dimuat ({len(data)} bytes)")
        except Exception as e:
            st.error("Gagal membaca file yang di-upload.")
            st.exception(e)

# If session_state has the uploaded bytes, show info and allow analyze
if st.session_state.get("uploaded_bytes"):
    name = st.session_state["uploaded_name"]
    data = st.session_state["uploaded_bytes"]
    mime = st.session_state.get("uploaded_type", "")
    st.write("Nama :", name)
    st.write("Tipe :", mime)
    st.write("Ukuran :", len(data), "bytes")

    # Optional: warn when file is large (adjust threshold sesuai hosting)
    max_allowed = 200 * 1024 * 1024  # 200 MB
    if len(data) > max_allowed:
        st.error("File terlalu besar untuk diproses di sini (>200MB).")
    else:
        if st.button("📄 Analyze Document"):
            # instantiate analyzer here to avoid heavy startup work
            analyzer = DocumentAnalyzer(api_key)

            # create wrapper to call existing extract_text(uploaded_file)
            wrapper = UploadedBytesWrapper(name, data, mime)

            try:
                with st.spinner("Extracting text..."):
                    document_text = extract_text(wrapper)
            except Exception as e:
                st.error("Gagal mengekstrak teks dari dokumen.")
                st.exception(e)
                st.write("Traceback:")
                st.text(traceback.format_exc())
                st.stop()

            if not document_text or not document_text.strip():
                st.error("No readable text found in the document. Jika ini scan (gambar), gunakan OCR.")
                st.stop()

            try:
                with st.spinner("Analyzing document..."):
                    result_json = analyzer.analyze(document_text)
            except Exception as e:
                st.error("Gagal memanggil analyzer.")
                st.exception(e)
                st.write("Traceback:")
                st.text(traceback.format_exc())
                st.stop()

            try:
                result = parse_response(result_json)
            except Exception:
                st.error("Model tidak mengembalikan JSON valid.")
                st.code(result_json)
                st.stop()

            st.success("Analysis completed!")
            st.subheader("📝 Executive Summary")
            st.write(result.get("summary", ""))
