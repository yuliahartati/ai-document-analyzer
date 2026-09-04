from io import BytesIO

from PyPDF2 import PdfReader
from docx import Document


def read_pdf(uploaded_file):
    """
    Extract text from a PDF file.
    """

    reader = PdfReader(BytesIO(uploaded_file.read()))

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text.strip()


def read_docx(uploaded_file):
    """
    Extract text from a DOCX file.
    """

    document = Document(BytesIO(uploaded_file.read()))

    paragraphs = []

    for paragraph in document.paragraphs:

        if paragraph.text.strip():

            paragraphs.append(paragraph.text)

    return "\n".join(paragraphs)


def extract_text(uploaded_file):
    """
    Detect file type and extract text.
    """

    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        return read_pdf(uploaded_file)

    if filename.endswith(".docx"):
        return read_docx(uploaded_file)

    raise ValueError(
        "Unsupported file type. Please upload a PDF or DOCX document."
    )
