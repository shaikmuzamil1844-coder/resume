import io
import logging

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_INSTALLED = True
except (ImportError, OSError):
    WEASYPRINT_INSTALLED = False

logger = logging.getLogger('ats_resume_scorer')

def generate_combined_pdf(html_docs: dict[str, str]) -> bytes:
    if WEASYPRINT_INSTALLED:
        try:
            documents = []
            for name, html_str in html_docs.items():
                doc = HTML(string=html_str).render()
                documents.append(doc)
            
            if documents:
                first_doc = documents[0]
                for other_doc in documents[1:]:
                    for page in other_doc.pages:
                        first_doc.pages.append(page)
                return first_doc.write_pdf()
        except Exception as exc:
            logger.warning(f"WeasyPrint rendering failed ({exc}), falling back to xhtml2pdf")

    # Fallback to pure-Python xhtml2pdf (works everywhere including Windows without external GTK/Pango C libraries)
    try:
        from xhtml2pdf import pisa
        from pypdf import PdfWriter

        writer = PdfWriter()
        for name, html_str in html_docs.items():
            buf = io.BytesIO()
            pisa_status = pisa.CreatePDF(html_str, dest=buf)
            if pisa_status.err:
                logger.warning(f"xhtml2pdf warning on {name}: {pisa_status.err}")
            buf.seek(0)
            writer.append(buf)

        final_buf = io.BytesIO()
        writer.write(final_buf)
        return final_buf.getvalue()
    except Exception as exc:
        logger.error(f"Failed to generate PDF with fallback engine: {exc}")
        raise RuntimeError(f"PDF generation failed: {exc}")
