import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Incident Intelligence Platform", layout="wide")
st.title("AI Incident Intelligence Platform")

tab_analyze, tab_kb = st.tabs(["Analyze", "Knowledge Base"])


with tab_analyze:
    st.write("Upload logs and/or a screenshot, or just describe what happened.")

    col1, col2 = st.columns(2)
    with col1:
        log_files = st.file_uploader(
            "Log files", type=["log", "txt", "csv"], accept_multiple_files=True
        )
    with col2:
        image_files = st.file_uploader(
            "Screenshots", type=["png", "jpg", "jpeg"], accept_multiple_files=True
        )

    description = st.text_area("Description (optional)", placeholder="What happened?")

    if st.button("Analyze", type="primary"):
        if not log_files and not image_files and not description.strip():
            st.error("Provide at least one log file, screenshot, or a description.")
        else:
            with st.spinner("Analyzing - this can take a minute..."):
                files = []
                for f in log_files or []:
                    files.append(("logs", (f.name, f.getvalue(), f.type)))
                for f in image_files or []:
                    files.append(("images", (f.name, f.getvalue(), f.type)))

                try:
                    response = requests.post(
                        f"{API_URL}/analyze",
                        data={"description": description} if description.strip() else {},
                        files=files if files else None,
                        timeout=180,
                    )
                except requests.exceptions.ConnectionError:
                    st.error(f"Can't reach the API at {API_URL}. Is `uvicorn api.main:app` running?")
                    st.stop()

            if response.status_code != 200:
                st.error(f"Request failed ({response.status_code}): {response.text}")
            else:
                result = response.json()
                llm = result["llm_analysis"]
                evidence = result["evidence_summary"]

                if llm.get("insufficient_evidence"):
                    st.warning(llm.get("reason", "Not enough evidence to produce a confident analysis."))
                elif llm.get("parse_failed"):
                    st.error("The model's response couldn't be parsed. Try again or check the backend logs.")
                else:
                    sev_color = {"Critical": "red", "High": "orange", "Medium": "blue", "Low": "green"}
                    sev = llm.get("severity", "Unknown")
                    st.markdown(f"### {llm.get('category', 'Unknown')} — :{sev_color.get(sev, 'gray')}[{sev}]")

                    if result.get("classifier"):
                        st.caption(
                            f"Classifier agrees: {result['classifier']['category']} "
                            f"({result['classifier']['confidence']:.0%} confidence)"
                        )

                    st.write(llm.get("summary", ""))

                    st.subheader("Root cause")
                    for rc in llm.get("root_causes", []):
                        st.markdown(f"**{rc['hypothesis']}** (confidence: {rc.get('confidence', 0):.0%})")
                        for ev in rc.get("evidence", []):
                            mark = "✅" if ev.get("verified") else "⚠️ unverified"
                            st.markdown(f"- {mark} `{ev['type']}`: {ev['ref']}")

                    if llm.get("recommendations"):
                        st.subheader("Recommendations")
                        for rec in llm["recommendations"]:
                            st.markdown(f"- {rec.get('action', '')} — *{rec.get('rationale', '')}*")

                    check = llm.get("citation_check", {})
                    if check:
                        st.caption(
                            f"Citation check: {check['total'] - check['unverified']}/{check['total']} verified"
                        )

                with st.expander("Evidence summary"):
                    st.json(evidence)


with tab_kb:
    st.write("Add runbooks or past-incident writeups so analyses can cite them.")

    try:
        status = requests.get(f"{API_URL}/kb/status", timeout=10).json()
        st.caption(f"Knowledge base currently has {status['total_chunks']} chunks.")
    except requests.exceptions.ConnectionError:
        st.caption("Can't reach the API to check KB status.")

    doc_file = st.file_uploader("Document (.md or .txt)", type=["md", "txt"], key="kb_upload")
    if st.button("Ingest") and doc_file is not None:
        with st.spinner("Ingesting..."):
            try:
                response = requests.post(
                    f"{API_URL}/kb/ingest",
                    files={"file": (doc_file.name, doc_file.getvalue())},
                    timeout=60,
                )
            except requests.exceptions.ConnectionError:
                st.error(f"Can't reach the API at {API_URL}.")
                st.stop()

        if response.status_code == 200:
            body = response.json()
            st.success(f"Added {body['chunks_added']} chunks from {body['filename']}.")
        else:
            st.error(f"Ingest failed: {response.text}")
