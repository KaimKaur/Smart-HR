ALLOWED_RESUME_MIMES = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
)


def detect_resume_mime(header: bytes) -> str | None:
    if header.startswith(b"%PDF"):
        return "application/pdf"
    if header[:4] == b"PK\x03\x04":
        return (
            "application/vnd.openxmlformats-officedocument"
            ".wordprocessingml.document"
        )
    return None


def extension_for_mime(mime: str) -> str:
    if mime == "application/pdf":
        return ".pdf"
    return ".docx"
