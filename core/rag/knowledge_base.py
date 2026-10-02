import os
import uuid

import chromadb
from sentence_transformers import SentenceTransformer
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBEDDING_MODEL_NAME, device="cpu")
    return _embedder


def chunk_text(text, chunk_size=400, overlap_ratio=0.12):
    """Splits a document into overlapping word chunks. Overlap matters so
    a sentence that gets cut in half at a chunk boundary still shows up
    whole in the neighboring chunk - otherwise you can lose the exact
    detail that would've answered the query.
    """
    words = text.split()
    if not words:
        return []

    overlap = int(chunk_size * overlap_ratio)
    step = chunk_size - overlap

    chunks = []
    for start in range(0, len(words), step):
        chunk_words = words[start:start + chunk_size]
        chunks.append(" ".join(chunk_words))
        if start + chunk_size >= len(words):
            break

    return chunks


class KnowledgeBase:
    """Thin wrapper around a ChromaDB collection. Handles ingesting
    documents (chunk -> embed -> store) and searching them.
    """

    def __init__(self, persist_path="data/chroma", collection_name="kb_chunks"):
        self.client = chromadb.PersistentClient(path=persist_path)
        self.collection = self.client.get_or_create_collection(collection_name)
        self.embedder = get_embedder()

    def ingest_document(self, text, source, doc_type="runbook", extra_metadata=None):
        """Chunks a document and adds every chunk to the collection.
        source is something like a filename, shows up in citations later
        so root causes can point back to exactly where the info came from.
        """
        chunks = chunk_text(text)
        if not chunks:
            return 0

        embeddings = self.embedder.encode(chunks).tolist()
        ids = [str(uuid.uuid4()) for _ in chunks]

        metadata = extra_metadata or {}
        metadatas = [
            {"source": source, "doc_type": doc_type, "chunk_index": i, **metadata}
            for i in range(len(chunks))
        ]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
        return len(chunks)

    def ingest_file(self, path, doc_type="runbook"):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        source = os.path.basename(path)
        return self.ingest_document(text, source=source, doc_type=doc_type)

    def search(self, query, top_k=5):
        """Returns the top_k most relevant chunks for a query, each with
        its source and a distance score (lower = more similar). FR-16.
        """
        query_embedding = self.embedder.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
        )

        hits = []
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for doc, meta, distance in zip(documents, metadatas, distances):
            hits.append({
                "text": doc,
                "source": meta.get("source"),
                "doc_type": meta.get("doc_type"),
                "distance": round(distance, 4),
            })

        return hits

    def count(self):
        return self.collection.count()


if __name__ == "__main__":
    kb = KnowledgeBase(persist_path="/tmp/test_kb_manual")

    kb.ingest_document(
        "When a DataNode reports repeated block termination errors, check "
        "disk health first with smartctl. A failing disk often shows up "
        "as intermittent block write failures before it fails completely.",
        source="runbook_datanode.md",
    )
    kb.ingest_document(
        "SSH authentication failures from an unfamiliar IP range usually "
        "indicate a brute-force attempt. Check /var/log/auth.log for the "
        "source IP and consider adding it to a fail2ban block list.",
        source="runbook_ssh.md",
    )

    print(f"kb has {kb.count()} chunks\n")

    results = kb.search("DataNode keeps terminating blocks, disk maybe failing?")
    for r in results[:2]:
        print(f"[{r['distance']}] {r['source']}: {r['text'][:80]}...")
