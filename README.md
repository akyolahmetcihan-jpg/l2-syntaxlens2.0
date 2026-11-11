# L2-SyntaxLens

Explainable, rule-based diagnostics for morphosyntactic and collocational errors in L2 English, built on
Universal Dependencies parses (spaCy). Every flag is traceable to a dependency relation and an explicit rule,
and is returned as typed JSON.

> Developed as a computational-linguistics portfolio project, with possible Turkish (L1) transfer notes.

## Features
- 12 deterministic rules: subject–verb agreement, verb–preposition collocation, tense and present-perfect
  clashes with past adverbials, do-support/modal complementation, double negation, countability, adjective order,
  a/an, double comparatives, since/for, numeral–plural agreement.
- In-text highlighting, dependency trees, token table, per-rule execution trace, JSON export.
- **Possible L1 (Turkish) transfer notes** for each rule (hypotheses based on contrastive typology).
- Pydantic v2 schemas, modular rule registry (`@rule`), test suite and evaluation script.

## Project structure
```
app.py                  Streamlit interface
syntaxlens/engine.py    Rules, schemas, analysis engine
syntaxlens/l1.py        Turkish L1-transfer explanations
eval/gold.csv           Annotated evaluation sentences
eval/evaluate.py        Per-rule precision / recall / F1 -> eval/results.md
tests/test_engine.py    pytest suite
```

## Run locally
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements-dev.txt
streamlit run app.py
```
Use Python 3.12 (newer versions may lack wheels for spaCy's dependencies).

## Test and evaluate
```bash
python -m pytest -q
python eval/evaluate.py
```

## Adding a rule
```python
@rule("MYRULE", "Category")
def my_rule(sent):
    for t in sent:
        if ...:
            yield Hit([t], "suggested fix", "Why this is an error.")
```
Then add an L1 note in `l1.py` and annotated sentences in `eval/gold.csv`.

## Limitations
- Rules depend on the accuracy of `en_core_web_sm`; parses of ungrammatical input can be wrong.
- Coverage is limited to the modelled phenomena; "no issues" does not mean "grammatical".
- The evaluation set is small and hand-written; results are indicative, not a benchmark.
- L1 notes are possible explanations, not verified causes for a given learner.

## Roadmap
Larger annotated corpus (e.g. W&I+LOCNESS), error-type taxonomy alignment (ERRANT), batch/CSV analysis.

## License
MIT
