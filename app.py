import html
import time
from dataclasses import dataclass
from typing import Callable, Iterator, List

import spacy
import streamlit as st
import streamlit.components.v1 as components
from pydantic import BaseModel, Field
from spacy import displacy

st.set_page_config(page_title="L2-SyntaxLens", page_icon="🔎", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@500;600&family=JetBrains+Mono:wght@400;500&display=swap');
h1, h2, h3 { font-family: 'Source Serif 4', Georgia, serif !important; letter-spacing: -0.01em; }
.sent { font-family: 'Source Serif 4', Georgia, serif; font-size: 1.45rem; line-height: 1.7;
        padding: 18px 22px; background: rgba(128,128,128,0.10); border: 1px solid rgba(128,128,128,0.35); border-radius: 6px; }
.sent mark { background: rgba(251,146,60,0.30); color: inherit; padding: 1px 4px; border-bottom: 2px solid #fb923c; border-radius: 2px; }
.issue { background: rgba(128,128,128,0.10); border: 1px solid rgba(128,128,128,0.35); border-left: 4px solid #fb923c;
         padding: 14px 18px; border-radius: 4px; margin-bottom: 10px; }
.issue .meta { font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; opacity: .65; }
.issue .title { font-weight: 600; font-size: 1.02rem; margin: 2px 0 8px; }
.issue code { font-family: 'JetBrains Mono', monospace; font-size: .85rem; background: rgba(128,128,128,0.22); padding: 1px 6px; border-radius: 3px; }
.issue .why { opacity: .85; font-size: .88rem; margin-top: 8px; }
table.tok { width: 100%; border-collapse: collapse; font-size: .88rem; }
table.tok th { text-align: left; background: rgba(128,128,128,0.18); padding: 6px 10px; border-bottom: 1px solid rgba(128,128,128,0.35); }
table.tok td { padding: 5px 10px; border-bottom: 1px solid rgba(128,128,128,0.25); font-family: 'JetBrains Mono', monospace; }
.ok { background: rgba(34,197,94,0.15); border: 1px solid rgba(34,197,94,0.5); padding: 12px 16px; border-radius: 4px; }
.trace { font-family: 'JetBrains Mono', monospace; font-size: .82rem; background: #1c1917; color: #e7e5e4;
         padding: 16px; border-radius: 6px; white-space: pre-wrap; }
</style>
""", unsafe_allow_html=True)



from syntaxlens.engine import RULES, analyze, highlighted


# ---------- UI ----------
PRESETS = {
    "Subject–verb agreement": "He go to the university library every afternoon.",
    "Plural subject": "The students goes to class and the teachers is late.",
    "Mass noun": "The professor gave us many useful informations.",
    "Adjective order": "She bought a red big backpack yesterday.",
    "Preposition": "Many students depend of their family for tuition.",
    "Tense clash": "She writes an academic essay yesterday.",
    "Do-support": "The applicant does not has enough credits.",
    "Double negation": "The student didn't write nothing during the lecture.",
    "Article": "He is an university student and wants a answer.",
    "Double comparative": "This exam is more easier than the last one.",
    "Since / for": "I have lived here since three years.",
    "Numeral + plural": "She has three brother and two sister.",
    "Perfect + past adverb": "I have seen him yesterday.",
    "Multi-sentence": "She don't like coffee. They was happy last week. I discussed about the plan.",
    "Well-formed": "The researcher depends on primary data and gathered significant evidence.",
}

with st.sidebar:
    st.markdown("### L2-SyntaxLens")
    st.caption("Rule-based diagnostics for L2 English, built on Universal Dependencies.")
    preset = st.selectbox("Example sentences", list(PRESETS))
    show_l1 = st.checkbox("Show possible Turkish (L1) transfer notes", value=True)
    st.markdown("**Rules**")
    for rid, cat, fn in RULES:
        st.markdown(f"- `{rid}` · {cat}")

st.title("L2-SyntaxLens")
st.caption("Paste learner text. Every flag is traceable to a dependency relation and an explicit rule.")

text = st.text_area("Learner text", value=PRESETS[preset], height=110, key=f"in_{preset}")

if text.strip():
    report, doc = analyze(text.strip())

    c1, c2, c3 = st.columns(3)
    c1.metric("Sentences", report.sentence_count)
    c2.metric("Issues", report.issue_count)
    c3.metric("Latency", f"{report.latency_ms} ms")

    st.markdown(f'<div class="sent">{highlighted(doc, report.issues)}</div>', unsafe_allow_html=True)
    st.write("")

    tab_d, tab_t, tab_k, tab_j, tab_l = st.tabs(["Diagnostics", "Dependency tree", "Tokens", "JSON", "Trace"])

    with tab_d:
        if not report.issues:
            st.markdown('<div class="ok">No violations found within the modelled rules.</div>', unsafe_allow_html=True)
        for iss in report.issues:
            l1_html = (f'<div class="why"><b>Possible L1 (Turkish) transfer:</b> {html.escape(iss.l1_note)}</div>'
                       if show_l1 and iss.l1_note else "")
            st.markdown(f"""
            <div class="issue">
              <div class="meta">{html.escape(iss.category)} · {iss.rule_id} · sentence {iss.sentence_index + 1}</div>
              <div class="title"><code>{html.escape(iss.focus)}</code> → <code>{html.escape(iss.fix)}</code></div>
              <div class="why">{html.escape(iss.explanation)}</div>
              {l1_html}
            </div>""", unsafe_allow_html=True)

    with tab_t:
        for sent in doc.sents:
            svg = displacy.render(sent.as_doc(), style="dep",
                                  options={"compact": True, "distance": 105, "bg": "transparent",
                                           "color": "inherit", "font": "JetBrains Mono"})
            st.markdown(f'<div style="overflow-x:auto">{svg.replace(chr(10), "")}</div>',
                        unsafe_allow_html=True)

    with tab_k:
        cols = ["Token", "Lemma", "UPOS", "XPOS", "Dep", "Head", "Morph"]
        rows = "".join(
            "<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in (
                t.text, t.lemma_, t.pos_, t.tag_, t.dep_, t.head.text, str(t.morph) or "—")) + "</tr>"
            for t in doc)
        head = "".join(f"<th>{c}</th>" for c in cols)
        st.markdown(f'<table class="tok"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>',
                    unsafe_allow_html=True)

    with tab_j:
        payload = report.model_dump_json(indent=2)
        st.download_button("Download JSON", payload, "syntaxlens_report.json", "application/json")
        st.code(payload, language="json")

    with tab_l:
        st.markdown(f'<div class="trace">{html.escape(chr(10).join(report.trace))}</div>', unsafe_allow_html=True)
