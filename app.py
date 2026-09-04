import streamlit as st

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
    "Upload a PDF or DOCX document to generate summaries, extract key insights, facts, claims, and action items."
)

api_key = st.secrets.get("OPENAI_API_KEY", None)

if not api_key:
    st.error("OPENAI_API_KEY not found.")
    st.stop()

analyzer = DocumentAnalyzer(api_key)

uploaded_file = st.file_uploader(
    "Upload Document",
    type=["pdf", "docx"],
    key="document_upload",
    accept_multiple_files=False
)

if uploaded_file:

    st.success(f"Loaded: {uploaded_file.name}")

    if st.button("📄 Analyze Document"):

        with st.spinner("Extracting text..."):

            document_text = extract_text(uploaded_file)

        if not document_text.strip():

            st.error("No readable text found in the document.")

            st.stop()

        with st.spinner("Analyzing document..."):

            result_json = analyzer.analyze(document_text)

        try:

            result = parse_response(result_json)

            st.success("Analysis completed!")

            st.subheader("📝 Executive Summary")

            st.write(result["summary"])

            sections = [
                ("💡 Key Insights", "key_insights"),
                ("✅ Facts", "facts"),
                ("📣 Claims", "claims"),
                ("📌 Action Items", "action_items")
            ]

            for title, key in sections:

                with st.expander(
                    f"{title} ({item_count(result[key])})",
                    expanded=False
                ):

                    if result[key]:

                        for item in result[key]:

                            st.markdown(f"- {item}")

                    else:

                        st.info("No items found.")

            report = build_markdown_report(result)

            st.download_button(
                "📄 Download Markdown Report",
                report,
                file_name="document_analysis.md",
                mime="text/markdown"
            )

            with st.expander("📄 Extracted Text"):

                st.text(document_text)

        except Exception:

            st.error("Model did not return valid JSON.")

            st.code(result_json)
