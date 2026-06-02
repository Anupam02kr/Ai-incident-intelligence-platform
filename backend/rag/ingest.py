from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.retriever import get_vector_store

_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)


def load_docs(path: Path):
    ext = path.suffix.lower()
    if ext == ".pdf":
        return PyPDFLoader(str(path)).load()
    if ext in (".txt", ".md", ".log"):
        return TextLoader(str(path), encoding="utf-8").load()
    raise ValueError(f"can't ingest {ext}")


def ingest_file(path: Path) -> int:
    chunks = _splitter.split_documents(load_docs(path))
    for c in chunks:
        c.metadata["source"] = path.name
    get_vector_store().add_documents(chunks)
    return len(chunks)


def ingest_folder(directory: Path) -> dict[str, int]:
    counts = {}
    for pattern in ("*.pdf", "*.txt", "*.md"):
        for p in directory.glob(pattern):
            counts[p.name] = ingest_file(p)
    return counts
