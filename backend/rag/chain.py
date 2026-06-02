from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from config import get_settings
from rag.retriever import get_vector_store

PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You help on-call engineers. Stick to the runbook excerpts. Say if you're guessing."),
    ("human", "Question: {question}\n\nRunbook:\n{context}"),
])


class RunbookQA:
    def __init__(self):
        cfg = get_settings()
        store = get_vector_store()
        self.retriever = store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": cfg.rag_top_k},
        )
        self.cfg = cfg
        self.parser = StrOutputParser()

    def query(self, question: str, extra_context: str | None = None) -> dict:
        docs = self.retriever.invoke(question)
        context = _join_docs(docs)
        if extra_context:
            context += f"\n\nFrom this incident:\n{extra_context[:2000]}"

        llm = self._openai()
        if llm:
            chain = (
                {"context": lambda _: context, "question": RunnablePassthrough()}
                | PROMPT
                | llm
                | self.parser
            )
            answer = chain.invoke(question)
        else:
            answer = _offline_answer(question, docs)

        return {
            "answer": answer,
            "sources": [
                {"source": d.metadata.get("source", "?"), "snippet": d.page_content[:280]}
                for d in docs
            ],
        }

    def _openai(self):
        if self.cfg.llm_provider != "openai" or not self.cfg.openai_api_key:
            return None
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.2, api_key=self.cfg.openai_api_key)


def _join_docs(docs) -> str:
    if not docs:
        return "(nothing in the index yet)"
    out = []
    for i, d in enumerate(docs, 1):
        src = d.metadata.get("source", "doc")
        out.append(f"[{i}] {src}\n{d.page_content}")
    return "\n\n".join(out)


def _offline_answer(question: str, docs) -> str:
    if not docs:
        return "No runbooks matched. Upload docs to /api/rag/ingest first."

    bits = []
    for d in docs[:3]:
        first_line = d.page_content.strip().split("\n", 1)[0][:160]
        bits.append(f"- {d.metadata.get('source', 'doc')}: {first_line}")

    return f"Question: {question}\n\nClosest docs:\n" + "\n".join(bits)
