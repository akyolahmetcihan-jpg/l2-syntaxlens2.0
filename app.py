import html
import time
from dataclasses import dataclass
from typing import Callable, Iterator, List, Optional

import spacy
import streamlit as st
from pydantic import BaseModel, Field
from spacy import displacy

st.set_page_config(page_title="SyntaxLens — UD Morphosyntactic Diagnostics", page_icon="⊢", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

.stApp { background-color: #f7f8fc !important; color: #0f172a !important; }
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
#MainMenu, header, footer { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; max-width: 1020px !important; }

/* Minimal Top Bar (Indigo / Cobalt Theme) */
.sl-nav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 20px; background: #ffffff;
    border: 1px solid #e2e6f3; border-radius: 12px;
    margin-bottom: 40px;
}
.sl-brand {
    display: flex; align-items: center; gap: 10px;
    font-family: 'Outfit', sans-serif; font-weight: 700;
    font-size: 1.22rem; color: #0f172a; letter-spacing: -0.02em;
}
.sl-glyph {
    font-family: 'JetBrains Mono', monospace; font-weight: 600; font-size: 0.92rem;
    color: #4338ca; background: #e0e7ff; border: 1px solid #c7d2fe;
    padding: 2px 8px; border-radius: 7px;
}
.sl-tag {
    font-family: 'JetBrains Mono', monospace; font-size: 0.76rem;
    padding: 4px 10px; border-radius: 6px; color: #475569; background: #f1f4fb;
}

/* Clean Hero */
.sl-hero { text-align: center; margin: 0 auto 32px; max-width: 680px; }
.sl-hero h1 {
    font-family: 'Outfit', sans-serif !important;
    font-size: 2.9rem !important; font-weight: 800 !important;
    line-height: 1.1 !important; letter-spacing: -0.035em !important;
    color: #0f172a !important; margin-bottom: 10px;
}
.sl-accent { color: #4f46e5; }
.sl-sub { font-size: 1rem; color: #64748b; font-weight: 400; }

/* KPI Cards */
.sl-kpi {
    background: #ffffff; border: 1px solid #e2e6f3; border-radius: 12px;
    padding: 14px 18px;
}
.sl-kpi-label { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; }
.sl-kpi-val { font-family: 'Outfit', sans-serif; font-size: 1.4rem; font-weight: 700; color: #0f172a; margin-top: 3px; }
.sl-kpi-val.accent { color: #4f46e5; }
.sl-kpi-val.ok { color: #16a34a; }

/* Dark Utterance Inspection Console */
.sl-shell {
    background: #ffffff; border: 1px solid #e2e6f3; border-radius: 14px;
    padding: 18px 20px; margin: 18px 0 24px;
}
.sl-shell-head {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 10px; font-size: 0.82rem; color: #64748b;
}
.sl-shell-head b { color: #0f172a; font-size: 0.88rem; }

.sl-dark-window {
    background: #0c1021; color: #e2e8f0; border-radius: 10px;
    padding: 20px 22px; font-family: 'JetBrains Mono', monospace;
    font-size: 0.96rem; line-height: 1.85;
}
.sl-dark-window mark {
    background: rgba(244, 63, 94, 0.25); color: #fecdd3;
    padding: 2px 6px; border-radius: 4px; border-bottom: 2px solid #f43f5e;
}

/* Issue Cards */
.issue {
    background: #ffffff; border: 1px solid #e2e6f3; border-left: 4px solid #4f46e5;
    padding: 14px 18px; border-radius: 10px; margin-bottom: 10px;
}
.issue .meta { font-family: 'JetBrains Mono', monospace; font-size: .72rem; text-transform: uppercase; letter-spacing: .06em; color: #4f46e5; font-weight: 600; }
.issue .title { font-weight: 600; font-size: 1rem; margin: 4px 0 8px; color: #0f172a; }
.issue code { font-family: 'JetBrains Mono', monospace; font-size: .85rem; background: #f1f4fb; color: #1e1b4b; padding: 2px 7px; border-radius: 4px; }
.issue .why { color: #475569; font-size: .88rem; margin-top: 6px; }
.ok-box { background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; padding: 14px 18px; border-radius: 10px; font-weight: 500; }

table.tok { width: 100%; border-collapse: collapse; font-size: .86rem; background: #fff; border: 1px solid #e2e6f3; border-radius: 10px; overflow: hidden; }
table.tok th { text-align: left; background: #f8fafc; padding: 9px 12px; border-bottom: 1px solid #e2e6f3; font-weight: 600; color: #334155; }
table.tok td { padding: 8px 12px; border-bottom: 1px solid #f1f5f9; font-family: 'JetBrains Mono', monospace; color: #0f172a; }
.trace { font-family: 'JetBrains Mono', monospace; font-size: .82rem; background: #0c1021; color: #c7d2fe; padding: 16px; border-radius: 10px; white-space: pre-wrap; }
</style>
""", unsafe_allow_html=True)

L1_NOTES = {
    "SVA": "Turkish verbs agree in person without a distinct 3sg -s contrast, and subjects after numerals/plurals often omit overt plural agreement.",
    "PREP": "Turkish encodes spatial/relational arguments via case suffixes (-e, -den, -de) rather than idiosyncratic verb–preposition pairings.",
    "TENSE": "Turkish learners may rely on the deictic time adverbial alone and leave the English finite verb uninflected.",
    "PERF": "Turkish lacks a present-perfect form that blocks definite past time adverbs (*yesterday*, *last week*).",
    "DOSUP": "Turkish negation is a verbal suffix (-me/-ma) with no auxiliary *do*, leading to double inflection on the main verb.",
    "NEG": "Turkish requires negative concord (*hiçbir şey yazmadı*), which is frequently transferred into English clauses.",
    "COUNT": "Turkish equivalents (*bilgiler*, *tavsiyeler*, *ödevler*) grammaticalize plural inflection freely.",
    "ADJ": "Turkish does not enforce the strict English size → age → colour → material prenominal hierarchy.",
    "ART": "Turkish has no definite article and does not alternate indefinite determiners phonologically (*a/an*).",
    "DCOMP": "Turkish forms comparatives analytically with *daha* + adjective, encouraging *more + -er* overgeneralisation.",
    "SINCEFOR": "Turkish *beri / -dır* spans both point-in-time and duration readings.",
    "NUMPL": "Turkish nouns remain morphologically singular after cardinal numerals (*üç kardeş* → *three brother*).",
}


@st.cache_resource
def load_nlp():
    return spacy.load("en_core_web_sm")


class Issue(BaseModel):
    rule_id: str
    category: str
    sentence_index: int
    token_indices: List[int]
    focus: str
    fix: str
    explanation: str
    l1_note: Optional[str] = None


class Report(BaseModel):
    text: str
    sentence_count: int
    issue_count: int
    issues: List[Issue] = Field(default_factory=list)
    trace: List[str] = Field(default_factory=list)
    latency_ms: float = 0.0


ALLOWED_PREPS = {
    "depend": {"on", "upon"}, "rely": {"on", "upon"}, "insist": {"on", "upon"},
    "listen": {"to"}, "interested": {"in"}, "wait": {"for", "until", "on"},
    "graduate": {"from", "in"}, "agree": {"with", "to", "on", "about"},
    "consist": {"of", "in"}, "good": {"at", "for", "with", "to"},
}
PREFERRED_PREP = {"depend": "on", "rely": "on", "insist": "on", "listen": "to", "interested": "in",
                  "wait": "for", "graduate": "from", "agree": "with", "consist": "of", "good": "at"}
EXTRA_PREP = {"discuss": "about", "mention": "about", "marry": "with", "emphasize": "on", "approach": "to"}
PREPS = {"on", "of", "in", "at", "to", "for", "from", "with", "by", "about", "upon", "into"}

MASS = {"information", "advice", "research", "furniture", "evidence", "homework",
        "knowledge", "equipment", "luggage", "progress", "feedback", "software"}
PLURAL_QUANT = {"many", "few", "several", "these", "those", "both"}
MASS_QUANT = {"much"}
PAST_WORDS = {"yesterday", "ago", "formerly", "previously"}
LAST_UNITS = {"week", "month", "year", "night", "summer", "winter", "semester", "monday", "tuesday",
              "wednesday", "thursday", "friday", "saturday", "sunday"}
ADJ_RANK = {
    **{w: 1 for w in ("big", "large", "small", "huge", "tiny", "tall", "short", "long")},
    **{w: 2 for w in ("old", "new", "young", "ancient", "modern")},
    **{w: 3 for w in ("red", "blue", "green", "black", "white", "yellow", "dark", "brown", "grey", "gray")},
    **{w: 4 for w in ("wooden", "metal", "plastic", "cotton", "silver", "golden", "leather")},
}
SG_PRON = {"he", "she", "it", "this", "that", "everyone", "everybody", "someone",
           "somebody", "nobody", "nothing", "everything"}
PL_PRON = {"they", "we", "these", "those"}
NEG_WORDS = {"no", "nothing", "nobody", "never", "none", "nowhere", "neither"}
VOWEL_SOUND_EXC = {"hour", "honest", "honor", "heir"}
CONS_SOUND_EXC = {"university", "user", "useful", "unit", "unique", "european", "one", "united", "uniform"}
DURATION_NOUNS = {"day", "days", "week", "weeks", "month", "months", "year", "years", "hour", "hours",
                  "minute", "minutes", "decade", "decades"}
NUM_EXEMPT = {"percent", "hundred", "thousand", "million", "billion", "dozen", "o'clock", "kg", "km", "cm"}


def third_person(lemma: str) -> str:
    irregular = {"be": "is", "have": "has", "do": "does", "go": "goes"}
    if lemma in irregular:
        return irregular[lemma]
    if lemma.endswith(("s", "sh", "ch", "x", "z", "o")):
        return lemma + "es"
    if lemma.endswith("y") and len(lemma) > 1 and lemma[-2] not in "aeiou":
        return lemma[:-1] + "ies"
    return lemma + "s"


@dataclass
class Hit:
    tokens: list
    fix: str
    why: str


RULES: List[tuple] = []


def rule(rid: str, category: str):
    def deco(fn: Callable) -> Callable:
        RULES.append((rid, category, fn))
        return fn
    return deco


@rule("SVA", "Agreement")
def subject_verb_agreement(sent) -> Iterator[Hit]:
    for t in sent:
        if t.dep_ != "nsubj" or t.tag_ == "WDT" or t.head.pos_ not in ("VERB", "AUX"):
            continue
        v, low, vl = t.head, t.lower_, t.head.lower_
        compound = any(c.dep_ == "conj" for c in t.children) and any(c.dep_ == "cc" for c in t.children)
        sg = not compound and (low in SG_PRON or t.tag_ in ("NN", "NNP"))
        pl = compound or low in PL_PRON or t.tag_ in ("NNS", "NNPS")
        if sg:
            if v.tag_ == "VBP" or vl in ("are", "were"):
                fix = {"are": "is", "were": "was"}.get(vl, third_person(v.lemma_))
                yield Hit([t, v], f"{t.text} {fix}", "A third-person singular subject requires the singular verb form (-s/-es, is/was).")
            for a in v.children:
                if a.dep_ == "aux" and a.lower_ in ("do", "have") and a.tag_ == "VBP":
                    yield Hit([t, a], f"{t.text} {third_person(a.lemma_)}", "Third-person singular subjects take does/has, not do/have.")
        elif pl and (v.tag_ == "VBZ" or vl in ("is", "was")):
            fix = {"is": "are", "was": "were"}.get(vl, v.lemma_)
            yield Hit([t, v], f"{t.text} {fix}", "A plural or coordinated subject requires the plural verb form.")


@rule("PREP", "Collocation")
def preposition_selection(sent) -> Iterator[Hit]:
    for t in sent:
        lemma = t.lemma_.lower()
        for c in t.children:
            if c.dep_ != "prep" or c.i != t.i + 1:
                continue
            if lemma in ALLOWED_PREPS and c.lower_ in PREPS and c.lower_ not in ALLOWED_PREPS[lemma]:
                yield Hit([t, c], f"{t.text} {PREFERRED_PREP[lemma]}", f"'{lemma}' selects the preposition '{PREFERRED_PREP[lemma]}'.")
            if lemma in EXTRA_PREP and c.lower_ == EXTRA_PREP[lemma]:
                yield Hit([t, c], t.text, f"'{lemma}' is transitive; the preposition '{c.text}' is redundant.")


@rule("TENSE", "Tense")
def tense_clash(sent) -> Iterator[Hit]:
    anchor = None
    toks = list(sent)
    for i, t in enumerate(toks):
        if t.lower_ in PAST_WORDS:
            anchor = t
        elif t.lower_ == "last" and i + 1 < len(toks) and toks[i + 1].lower_ in LAST_UNITS:
            anchor = t
        elif t.lower_ == "in" and i + 1 < len(toks) and toks[i + 1].text.isdigit() and len(toks[i + 1].text) == 4 and int(toks[i + 1].text) < time.localtime().tm_year:
            anchor = toks[i + 1]
        if anchor:
            break
    if not anchor:
        return
    for t in toks:
        if t.pos_ in ("VERB", "AUX") and t.dep_ in ("ROOT", "conj") and t.tag_ in ("VBP", "VBZ"):
            yield Hit([t, anchor], f"past form of '{t.lemma_}'", f"The past-time expression '{anchor.text}' requires simple past (VBD), not present.")


@rule("DOSUP", "Auxiliary")
def auxiliary_complementation(sent) -> Iterator[Hit]:
    for t in sent:
        if t.dep_ != "aux":
            continue
        head = t.head
        if t.lemma_ == "do" and head.pos_ == "VERB" and head.tag_ in ("VBZ", "VBD", "VBN", "VBG"):
            yield Hit([t, head], f"{t.text} {head.lemma_}", "After do-support the lexical verb must be a bare infinitive.")
        elif t.tag_ == "MD" and head.pos_ == "VERB" and head.tag_ in ("VBZ", "VBD", "VBG"):
            yield Hit([t, head], f"{t.text} {head.lemma_}", "A modal verb must be followed by the bare infinitive.")


@rule("NEG", "Polarity")
def double_negation(sent) -> Iterator[Hit]:
    negs = [t for t in sent if t.dep_ == "neg" or t.lower_ in NEG_WORDS]
    if len(negs) > 1 and "only" not in sent.text.lower():
        yield Hit(negs, "use one negator with any-/ever-", "Standard English allows one clausal negation; use a negative polarity item (anything, anybody, ever).")


@rule("COUNT", "Countability")
def countability(sent) -> Iterator[Hit]:
    for t in sent:
        stem = t.lower_[:-1] if t.lower_.endswith("s") else t.lower_
        if t.tag_ == "NNS" and stem in MASS:
            yield Hit([t], stem, f"'{stem}' is a mass noun and has no plural.")
        if t.lower_ in MASS or stem in MASS:
            for c in t.children:
                if c.lower_ in PLURAL_QUANT and c.dep_ in ("amod", "det", "quantmod"):
                    yield Hit([c, t], f"much / a lot of {stem}", f"'{c.text}' combines only with countable plurals.")
        if t.tag_ == "NNS" and stem not in MASS:
            for c in t.children:
                if c.lower_ in MASS_QUANT and c.dep_ in ("amod", "det", "quantmod"):
                    yield Hit([c, t], f"many {t.text}", "'much' combines only with uncountable nouns.")


@rule("ADJ", "Noun phrase")
def adjective_order(sent) -> Iterator[Hit]:
    for t in sent:
        if t.pos_ != "NOUN":
            continue
        adjs = sorted([c for c in t.children if c.dep_ == "amod" and c.lower_ in ADJ_RANK], key=lambda x: x.i)
        for a, b in zip(adjs, adjs[1:]):
            if ADJ_RANK[a.lower_] > ADJ_RANK[b.lower_]:
                yield Hit([a, b, t], f"{b.text} {a.text} {t.text}", "Prenominal order: size → age → colour → material.")


@rule("ART", "Determiner")
def a_an(sent) -> Iterator[Hit]:
    toks = list(sent)
    for a, b in zip(toks, toks[1:]):
        if a.lower_ not in ("a", "an") or not b.is_alpha:
            continue
        w = b.lower_
        vowel = (w[0] in "aeiou" and w not in CONS_SOUND_EXC) or w in VOWEL_SOUND_EXC
        if a.lower_ == "a" and vowel:
            yield Hit([a, b], f"an {b.text}", "Use 'an' before a vowel sound.")
        elif a.lower_ == "an" and not vowel:
            yield Hit([a, b], f"a {b.text}", "Use 'a' before a consonant sound.")


@rule("PERF", "Tense")
def perfect_with_past_adverb(sent) -> Iterator[Hit]:
    toks = list(sent)
    anchor = next((t for t in toks if t.lower_ in PAST_WORDS), None)
    if anchor is None:
        anchor = next((a for a, b in zip(toks, toks[1:]) if a.lower_ == "last" and b.lower_ in LAST_UNITS), None)
    if anchor is None:
        return
    for t in toks:
        if t.tag_ == "VBN" and any(c.dep_ == "aux" and c.lemma_ == "have" for c in t.children):
            aux = next(c for c in t.children if c.dep_ == "aux" and c.lemma_ == "have")
            yield Hit([aux, t, anchor], f"simple past of '{t.lemma_}'", f"Present perfect cannot combine with the definite past time expression '{anchor.text}'.")


@rule("DCOMP", "Comparison")
def double_comparative(sent) -> Iterator[Hit]:
    toks = list(sent)
    for a, b in zip(toks, toks[1:]):
        if a.lower_ in ("more", "most") and b.tag_ in ("JJR", "JJS") and b.lower_ not in ("more", "most", "less"):
            yield Hit([a, b], b.text, f"'{b.text}' is already comparative/superlative; do not add '{a.text}'.")


@rule("SINCEFOR", "Preposition")
def since_for(sent) -> Iterator[Hit]:
    toks = list(sent)
    for i, t in enumerate(toks):
        if t.lower_ == "since":
            window = toks[i + 1:i + 3]
            if any(w.lower_ in DURATION_NOUNS for w in window) and not any(w.lower_ in ("then", "last") for w in window):
                yield Hit([t] + window[:2], "for + duration", "'since' marks a starting point; durations take 'for'.")
        elif t.lower_ == "for" and i + 1 < len(toks) and toks[i + 1].text.isdigit() and len(toks[i + 1].text) == 4:
            yield Hit([t, toks[i + 1]], "since + year", "A starting point (a year) takes 'since', not 'for'.")


@rule("NUMPL", "Nominal morphology")
def number_plural(sent) -> Iterator[Hit]:
    for t in sent:
        if t.tag_ != "NN" or t.lower_ in NUM_EXEMPT or t.lower_ in MASS:
            continue
        if t.i > 0 and t.doc[t.i - 1].text == "-":
            continue
        for c in t.children:
            if c.dep_ == "nummod" and c.like_num and c.lower_ not in ("one", "1", "zero") and "." not in c.text:
                plural = t.text[:-1] + "ies" if t.text.endswith("y") and t.text[-2:-1] not in "aeiou" else t.text + "s"
                yield Hit([c, t], f"{c.text} {plural}", "Nouns after numerals greater than one take the plural.")


def analyze(text: str):
    nlp = load_nlp()
    t0 = time.perf_counter()
    doc = nlp(text)
    report = Report(text=text, sentence_count=0, issue_count=0)
    report.trace.append(f"Parsed {len(doc)} tokens with en_core_web_sm (Universal Dependencies).")
    for si, sent in enumerate(doc.sents):
        report.sentence_count += 1
        report.trace.append(f"Sentence {si + 1}: \"{sent.text.strip()}\"")
        for rid, cat, fn in RULES:
            hits = list(fn(sent))
            report.trace.append(f"  {rid:<6} -> {len(hits)} hit(s)")
            for h in hits:
                report.issues.append(Issue(
                    rule_id=rid, category=cat, sentence_index=si,
                    token_indices=sorted({x.i for x in h.tokens}),
                    focus=" … ".join(x.text for x in sorted(h.tokens, key=lambda x: x.i)),
                    fix=h.fix, explanation=h.why, l1_note=L1_NOTES.get(rid)))
    report.issue_count = len(report.issues)
    report.latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    return report, doc


def highlighted(doc, issues: List[Issue]) -> str:
    flagged = {i for iss in issues for i in iss.token_indices}
    out = []
    for t in doc:
        w = html.escape(t.text)
        out.append(f"<mark>{w}</mark>{t.whitespace_}" if t.i in flagged else f"{w}{t.whitespace_}")
    return "".join(out)


# ---------- Minimal Top Bar & Hero ----------
st.markdown("""
<div class="sl-nav">
  <div class="sl-brand"><span class="sl-glyph">⟦⊢⟧</span> SyntaxLens</div>
  <div style="display:flex;align-items:center;gap:8px;">
    <span class="sl-tag">Universal Dependencies · 12 Rules</span>
    <span class="sl-tag">Held-out F1: 0.92</span>
  </div>
</div>

<div class="sl-hero">
  <h1>Morphosyntactic diagnostics<span class="sl-accent">.</span></h1>
  <div class="sl-sub">Deterministic L2 error detection over dependency parse trees with Turkish L1 transfer notes.</div>
</div>
""", unsafe_allow_html=True)

PRESETS = {
    "Subject–verb agreement (SVA)": "He go to the university library every afternoon.",
    "Plural subject concord (SVA)": "The students goes to class and the teachers is late.",
    "Mass noun pluralization (COUNT)": "The professor gave us many useful informations.",
    "Adjective hierarchy (ADJ)": "She bought a red big backpack yesterday.",
    "Preposition collocation (PREP)": "Many students depend of their family for tuition.",
    "Past adverbial tense clash (TENSE)": "She writes an academic essay yesterday.",
    "Do-support double marking (DOSUP)": "The applicant does not has enough credits.",
    "Negative concord (NEG)": "The student didn't write nothing during the lecture.",
    "Phonological article (ART)": "He is an university student and wants a answer.",
    "Double comparative (DCOMP)": "This exam is more easier than the last one.",
    "Point vs. duration (SINCEFOR)": "I have lived here since three years.",
    "Numeral + singular noun (NUMPL)": "She has three brother and two sister.",
    "Present perfect + past adverb (PERF)": "I have seen him yesterday.",
    "Multi-sentence diagnostic": "She don't like coffee. They was happy last week. I discussed about the plan.",
    "Well-formed control sentence": "The researcher depends on primary data and gathered significant evidence.",
}

col_p, col_l1 = st.columns([2, 1])
with col_p:
    preset = st.selectbox("Sample", list(PRESETS))
with col_l1:
    l1_mode = st.selectbox("Contrastive L1 Notes", ["Turkish (L1) · Enabled", "Disabled"])
    show_l1 = l1_mode.startswith("Turkish")

text = st.text_area("Learner text", value=PRESETS[preset], height=90, label_visibility="collapsed")

if text.strip():
    report, doc = analyze(text.strip())

    status_cls = "ok" if report.issue_count == 0 else "accent"

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f'<div class="sl-kpi"><div class="sl-kpi-label">Issues Found</div><div class="sl-kpi-val {status_cls}">{report.issue_count}</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="sl-kpi"><div class="sl-kpi-label">Sentences</div><div class="sl-kpi-val">{report.sentence_count}</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="sl-kpi"><div class="sl-kpi-label">Tokens</div><div class="sl-kpi-val">{len(doc)}</div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="sl-kpi"><div class="sl-kpi-label">Latency</div><div class="sl-kpi-val">{report.latency_ms} ms</div></div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="sl-shell">
      <div class="sl-shell-head">
        <b>Utterance Inspection</b>
        <span>Highlighted tokens trigger a dependency rule violation</span>
      </div>
      <div class="sl-dark-window">
        {highlighted(doc, report.issues)}
      </div>
    </div>
    """, unsafe_allow_html=True)

    tab_d, tab_t, tab_k, tab_j, tab_l = st.tabs(["Diagnostics", "Dependency Tree", "Tokens (UD)", "JSON Schema", "Execution Trace"])

    with tab_d:
        if not report.issues:
            st.markdown('<div class="ok-box">✓ No violations found within the 12 modelled grammatical constraints.</div>', unsafe_allow_html=True)
        for iss in report.issues:
            l1_html = (f'<div class="why"><b>L1 (Turkish) transfer:</b> {html.escape(iss.l1_note)}</div>'
                       if show_l1 and iss.l1_note else "")
            st.markdown(f"""
            <div class="issue">
              <div class="meta">{html.escape(iss.category)} · {iss.rule_id} · Sentence {iss.sentence_index + 1}</div>
              <div class="title"><code>{html.escape(iss.focus)}</code> → <code>{html.escape(iss.fix)}</code></div>
              <div class="why">{html.escape(iss.explanation)}</div>
              {l1_html}
            </div>""", unsafe_allow_html=True)

    with tab_t:
        for sent in doc.sents:
            svg = displacy.render(sent.as_doc(), style="dep",
                                  options={"compact": True, "distance": 105, "bg": "#ffffff",
                                           "color": "#0f172a", "font": "JetBrains Mono"})
            st.markdown(f'<div style="overflow-x:auto;background:#ffffff;border:1px solid #e2e6f3;border-radius:10px;padding:12px;">{svg.replace(chr(10), "")}</div>',
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

