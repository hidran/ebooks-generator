"""Localized title for a generated table of contents (EPUB toc.xhtml, DOCX TOC field)."""

TOC_TITLE = {
    "en": "Contents", "it": "Sommario", "es": "Índice", "fr": "Table des matières",
    "de": "Inhaltsverzeichnis", "pt": "Sumário", "nl": "Inhoud", "ca": "Índex",
}


def toc_title(lang):
    """'it-IT' → 'Sommario'; unknown languages fall back to 'Contents'."""
    return TOC_TITLE.get((lang or "en").split("-")[0].lower(), "Contents")
