# datadx (Data Diagnostics)

[![CI](https://github.com/thinkTinkerGreen/datadx/actions/workflows/ci.yml/badge.svg)](https://github.com/thinkTinkerGreen/datadx/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**`datadx`** is a state-of-the-art data diagnosis, curation, and provenance cleaning toolkit engineered for multilingual Large Language Model (LLM) pre-training corpora. It was purpose-built to diagnose and heal low-resource and Indic language datasets (such as Marathi, Hindi, Bengali) sourced from raw web scrapes (Common Crawl / FineWeb-2).

---

## 🩺 The Philosophy: Doctor, Disease, and Medicine

Training frontier models on dirty web scrapes degrades reasoning, blows up tokenizer fertility, and pollutes generation with web junk. `datadx` implements the clinical paradigm:
1. **Diagnosis:** Read the patient slice (e.g. 500 documents), identify disease symptoms with exact character offsets and evidence.
2. **Labeling:** Maintain strict provenance in standardized label sheets (`labels.csv`) without guessing (`NOT_CHECKED` guardrails).
3. **Prescription:** Propose deterministic, pure, and idempotent medicines in [`medicine.md`](docs/DISEASES.md).
4. **Harm Testing:** Prove that the medicine causes $< 1.0\%$ collateral damage against gold-standard clean sets before scaling.
5. **Provenance Audit:** Log every transformation into a dual-layer private/public audit Parquet (`audit_<pack_id>.parquet`).

---

## 🦠 Disease Catalog (Groups A through H)

`datadx` scans and diagnoses all canonical disease codes specified in `DISEASES.md`:

| Group | Codes | Category | Description & Indic Nuances |
|---|---|---|---|
| **A** | `A1`–`A6` | Characters | Invisible junk (U+200B, BOM), control codes, mojibake (`Ã¤`), replacement (``), NFC violations, and script agglutination (`Articleकसब्याच्या`). *ZWJ/ZWNJ strictly preserved.* |
| **B** | `B1`–`B5` | Markup & Ghost Tokens | HTML entities, raw tags, broken LaTeX, and ghost chat markers (`<\|im_start\|>`, `[INST]`, `<s>`). |
| **C** | `C1`–`C5` | Structure | Boilerplate menus, repeated lines, truncated text, merged documents, and SEO tag clouds. |
| **D** | `D1`–`D5` | Language | Wrong language label, Romanised Indic, natural vs unnatural code-mixing (evaluated sentence-by-sentence), bad machine translation, and translationese. |
| **E** | `E1`–`E6` | Code | Minified code, data blobs, secrets, repeated license headers, and broken encoding. |
| **F** | `F1`–`F3` | Safety & Contamination | PII (Aadhaar, PAN, phone numbers, emails), benchmark leakage (13-gram test set decontamination), and harmful content. |
| **G** | `G1`–`G4` | Indic Damage | Split matras (`त ि`), split visarga (`९ ः ३०`), lost eyelash-ra ZWJ (`ऱ`), English rule truncation, and ASCII pipe danda substitutions (`\|` $\rightarrow$ `।`). |
| **H** | `H1`–`H3` | Duplication | Bit-identical hash deduplication, character 5-gram Jaccard near-duplicates, and cross-lingual duplicates. |

---

## 🚀 Quick Start

### Installation

Requires Python 3.12+ and `uv` (recommended) or `pip`:

```bash
git clone https://github.com/thinkTinkerGreen/datadx.git
cd datadx
uv sync
```

Or install directly as a global CLI tool:
```bash
uv tool install git+https://github.com/thinkTinkerGreen/datadx.git
```

---

## 🛠️ CLI Commands Overview

The toolkit provides the unified `diagnose` CLI:

```text
diagnose view       View documents with invisible characters highlighted and hex dumps
diagnose scan       Scan a Parquet pack and output draft diagnostic labels
diagnose confirm    Batch promote clean candidate rows after human confirmation
diagnose medicine   Propose medicines and execute gold-set harm tests
diagnose audit      Generate private and public sanitized provenance audit Parquets
diagnose report     Generate comprehensive diagnostic markdown reports
diagnose export     Export a validated slice (e.g. first 150 rows) for submission milestones
diagnose run-all    Execute the full end-to-end diagnostic and audit pipeline
```

### Common Workflows

#### 1. End-to-End Pipeline Execution
```bash
uv run diagnose run-all ind-mr-fw2.parquet \
  --pack-id ind-mr-fw2 \
  --reads mr \
  --reader thinktinkergreen
```

#### 2. Inspecting Documents with the Advanced Viewer
```bash
# View documents with unicode escapes highlighted (\u200b)
uv run diagnose view ind-mr-fw2.parquet --rows 1-5

# View tail blocks and inspect hex dumps
uv run diagnose view ind-mr-fw2.parquet --rows 3 --tail --hex

# Inspect clean text and audit provenance from an audit parquet
uv run diagnose view runs/ind-mr-fw2/audit_ind-mr-fw2.parquet --rows 1-5
```

#### 3. Exporting Milestone Slices
```bash
# Export the first 150 rows with full schema validation
uv run diagnose export runs/ind-mr-fw2/labels_ind-mr-fw2.csv \
  --first 150 \
  --out diagnosis/submissions/ind-mr-fw2/thinktinkergreen/labels.csv
```

---

## ☁️ Google Colab Execution (Free Tier GPU)

The repository provides [`notebooks/colab_runner.ipynb`](notebooks/colab_runner.ipynb) optimized for Google Colab free-tier T4 GPUs:
- **50% GPU Memory Cap:** Uses `torch.cuda.set_per_process_memory_fraction(0.5)` to eliminate CUDA Out-Of-Memory (OOM) crashes.
- **Drive Persistence:** Automatically syncs runs, audit parquets, and reports to Google Drive (`MyDrive/data-diagnosis/`).
- **Complete Test Execution:** Runs full pytest suites and harm tests in the cloud environment.

---

## 🧪 Testing & Code Quality

`datadx` adheres to strict typing, deterministic reproducibility, and zero-compromise code hygiene:

```bash
# Lint with Ruff
make lint

# Typecheck with strict Mypy
make typecheck

# Execute tests (on Colab or designated test runner)
make test
```

---

## 📄 License

MIT License. Designed and maintained by [@thinktinkergreen](https://github.com/thinktinkergreen).
