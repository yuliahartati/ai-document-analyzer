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
        st.error("⚠️ Silakan masukkan Gemini API Key di menu sidebar samping kiri terlebih dahulu!")
    elif uploaded_file is None:
        st.error("⚠️ Silakan atur dan unggah file terlebih dahulu!")
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
st.caption("Tips HP Android: Jika aplikasi sering restart, buat file .streamlit/config.toml di repo GitHub kamu dengan opsi maxUploadSize = 200.")
