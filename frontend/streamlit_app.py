import json
import os

import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://localhost:3000")

st.set_page_config(page_title="RAG Tech Talk POC", page_icon="📚", layout="wide")


def api_get(path: str):
    with httpx.Client(base_url=API_BASE_URL, timeout=120.0) as client:
        response = client.get(path)
        response.raise_for_status()
        return response.json()


def api_post_json(path: str, payload: dict):
    with httpx.Client(base_url=API_BASE_URL, timeout=120.0) as client:
        response = client.post(path, json=payload)
        response.raise_for_status()
        return response.json()


def api_upload(file, strategy: str):
    with httpx.Client(base_url=API_BASE_URL, timeout=300.0) as client:
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": (file.name, file.getvalue(), file.type or "application/octet-stream")},
            data={"strategy": strategy},
        )
        response.raise_for_status()
        return response.json()


def stream_chat(question: str, rag_mode: str, rerank_enabled: bool):
    payload = {"question": question, "rag_mode": rag_mode, "rerank_enabled": rerank_enabled}
    with httpx.Client(base_url=API_BASE_URL, timeout=300.0) as client:
        with client.stream("POST", "/api/v1/chat/stream", json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line.startswith("data: "):
                    continue
                data = json.loads(line[6:])
                if data.get("done"):
                    payload = {}
                    if data.get("sources"):
                        payload["sources"] = data["sources"]
                    if data.get("trace_id"):
                        payload["trace_id"] = data["trace_id"]
                    if payload:
                        yield payload
                    break
                token = data.get("token")
                if token:
                    yield token


st.sidebar.title("RAG Tech Talk POC")
page = st.sidebar.radio("Navigation", ["Documents", "Chat"])

st.sidebar.markdown("---")
st.sidebar.caption(f"API: `{API_BASE_URL}`")
st.sidebar.caption(f"LangFuse: `{LANGFUSE_HOST}`")

if page == "Documents":
    st.title("Document Ingestion")
    st.markdown("Upload PDF or DOCX files. They are stored locally and chunked for retrieval.")

    strategy = st.selectbox(
        "Chunking strategy",
        ["fixed_size", "sliding_window", "semantic"],
        help="Compare chunking approaches during the tech talk demo.",
    )
    uploaded = st.file_uploader("Choose a file", type=["pdf", "docx"])

    if uploaded and st.button("Ingest document", type="primary"):
        with st.spinner("Parsing, chunking, and embedding..."):
            result = api_upload(uploaded, strategy)
        st.success(
            f"Ingested **{result['document']['filename']}** — "
            f"{result['chunks_created']} chunks ({result['strategy']})"
        )

    st.subheader("Ingested documents")
    try:
        documents = api_get("/api/v1/documents")
        if not documents:
            st.info("No documents yet. Upload a PDF or DOCX to get started.")
        else:
            for doc in documents:
                cols = st.columns([4, 2, 1])
                cols[0].write(f"**{doc['filename']}**")
                cols[1].write(f"{doc['chunk_count']} chunks")
                if cols[2].button("Delete", key=f"del_{doc['id']}"):
                    with httpx.Client(base_url=API_BASE_URL, timeout=60.0) as client:
                        client.delete(f"/api/v1/documents/{doc['id']}").raise_for_status()
                    st.rerun()
    except httpx.HTTPError as exc:
        st.error(f"Could not reach API: {exc}")

else:
    st.title("RAG Chat")
    rag_mode = st.selectbox("RAG mode", ["hybrid", "naive"], help="Compare naive vector-only vs hybrid search.")
    rerank_enabled = st.checkbox("Enable reranking", value=False)

    question = st.text_input("Ask a question about your documents")
    use_stream = st.checkbox("Stream response", value=True)

    if question and st.button("Ask", type="primary"):
        st.subheader("Answer")
        answer_box = st.empty()

        if use_stream:
            tokens = []
            sources = []
            trace_id = None
            for token in stream_chat(question, rag_mode, rerank_enabled):
                if isinstance(token, dict):
                    sources = token.get("sources", [])
                    trace_id = token.get("trace_id")
                    continue
                tokens.append(token)
                answer_box.markdown("".join(tokens))
            full_answer = "".join(tokens)

            if trace_id:
                st.markdown(f"[View trace in LangFuse]({LANGFUSE_HOST}/trace/{trace_id})")
        else:
            result = api_post_json(
                "/api/v1/chat",
                {"question": question, "rag_mode": rag_mode, "rerank_enabled": rerank_enabled},
            )
            full_answer = result["answer"]
            answer_box.markdown(full_answer)

            if result.get("trace_id"):
                st.markdown(f"[View trace in LangFuse]({LANGFUSE_HOST}/trace/{result['trace_id']})")

            st.subheader("Retrieved sources")
            for source in result.get("sources", []):
                with st.expander(
                    f"{source['filename']} | chunk {source['chunk_index']} | "
                    f"{source['source']} | score {source['score']:.4f}"
                ):
                    st.write(source["content"])

        if use_stream and sources:
            st.subheader("Retrieved sources")
            for source in sources:
                with st.expander(
                    f"{source['filename']} | chunk {source['chunk_index']} | "
                    f"{source['source']} | score {source['score']:.4f}"
                ):
                    st.write(source["content"])
