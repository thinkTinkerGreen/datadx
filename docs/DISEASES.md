# Data Diagnosis: Disease List and Label Sheet

You are the doctor. You read a sample pack. You find each disease. You give evidence. You propose a medicine.
You prove that the medicine does no harm. We run the medicine at scale. You do not run cleaning scripts on the
full data.

## 1. Your reading slice

Your reading slice is one sample pack: about 500 documents from one source, in one language or one programming
language. The pack is a Parquet file with the columns `doc_id`, `source`, `lang_label`, `text`.

Read each document. Use the viewer script (it shows each document with hidden characters made visible, and gives a
hex dump on request). Do not read only the first lines of a document. Long documents hide their diseases in the
middle and at the end.

## 2. The diseases

Each disease has a code. Use the code in your label sheet.

### A. Characters
| Code | Disease | How it looks | Notes |
|---|---|---|---|
| A1 | Invisible junk characters | zero-width space U+200B, BOM U+FEFF, bidi marks U+202A to U+202E, U+2066 to U+2069, soft hyphen U+00AD | **ZWJ U+200D and ZWNJ U+200C are NOT diseases in Indic text.** They are part of the script. |
| A2 | Control characters | U+0000 to U+001F (except tab and newline), U+007F to U+009F | |
| A3 | Mojibake | `Ã¤`, `à¤¹`, `â€™` | UTF-8 text decoded twice |
| A4 | Replacement characters | U+FFFD `�` | Bytes lost before release. Count them. |
| A5 | Wrong normal form | the same word in two byte forms; nukta written two ways | We use NFC. Report each case where NFC changes the meaning or the look. |
| A6 | Wrong or mixed script | Hindi text with Latin look-alike letters; a Bengali word in Assamese letters | |

### B. Markup and ghost tokens
| Code | Disease | How it looks |
|---|---|---|
| B1 | HTML entities | `&amp;`, `&nbsp;`, `&#2361;` |
| B2 | HTML or XML tags | `<div>`, `<br/>`, `</p>` |
| B3 | Ghost chat markers | `<|im_start|>`, `<|endoftext|>`, `[INST]`, `<s>`, `### Assistant:`, `<think>` |
| B4 | Template and code junk in prose | `{{ variable }}`, `${...}`, `undefined`, `NaN` |
| B5 | Markdown or LaTeX that is broken | an unclosed code fence, `\frac{` with no end |

B3 is the most dangerous disease. A ghost marker in pre-training text teaches the model to write our special tokens
as plain text.

### C. Document structure
| Code | Disease | How it looks |
|---|---|---|
| C1 | Boilerplate | menus, cookie banners, "Share on WhatsApp", footer links |
| C2 | Repeated lines | the same line many times in one document |
| C3 | Truncated document | the text stops in the middle of a sentence or a code block |
| C4 | Two documents joined | two unrelated texts with no boundary |
| C5 | Lists of keywords or links | SEO spam, tag clouds |

### D. Language
| Code | Disease | How it looks |
|---|---|---|
| D1 | Wrong language label | the label says Marathi, the text is Hindi |
| D2 | Romanised Indic | Hindi written in Latin letters |
| D3 | Mixed language | Hindi and English mixed in one sentence (note: this can be natural; label it, do not judge it) |
| D4 | Bad machine translation | wrong meaning, broken grammar, English words left untranslated, wrong gender or case |
| D5 | Translationese | grammatical, but no native speaker writes like this |

### E. Code (for code packs)
| Code | Disease | How it looks |
|---|---|---|
| E1 | Minified or generated code | one very long line; "auto-generated, do not edit" |
| E2 | Data blobs | base64, long number arrays, embedded images |
| E3 | Secrets | API keys, passwords, tokens, private keys |
| E4 | Repeated licence headers | the same 30-line licence text at the top of many files |
| E5 | Broken encoding in code | mojibake inside strings or comments |
| E6 | Not code | a README, a log file or a CSV labelled as code |

### F. Safety, privacy and contamination
| Code | Disease | How it looks |
|---|---|---|
| F1 | Personal data | emails, phone numbers, addresses, ID numbers of private people |
| F2 | Benchmark leak | a question or a solution from a benchmark test set |
| F3 | Harmful content | content that we must not train on |

### G. Damage from earlier cleaning (most important for Indic)
| Code | Disease | How it looks |
|---|---|---|
| G1 | Cut at the vowel sign | a word split before a matra or virama, for example `क ि` |
| G2 | Lost ZWJ or ZWNJ | a conjunct that renders wrong |
| G3 | Indic dropped by an English rule | a good document with a low "quality" score; whole sections missing |
| G4 | Over-normalised | NFKC changed the characters; digits changed from Indic to Latin |

### H. Duplicates
| Code | Disease | How it looks |
|---|---|---|
| H1 | Exact duplicate in the pack | |
| H2 | Near duplicate | the same text with small changes |
| H3 | The same content in another source or language | a translation of a document that you saw in English |

## 2a. Never copy personal data or secrets

The lab repository is public. For **F1 (personal data)** and **E3 (secrets)**, the `evidence` column gives only the
type and the position, for example `email at offset 64` or `AWS key at offset 2210`. **Never copy the value itself**
into any file, pull request or chat message. Leave the `hex` column empty for F1 and E3.

## 3. The label sheet

One row for each document that you read. Use the template file `labels_<slice_id>.csv`.

| Column | Content |
|---|---|
| `doc_id` | from the pack |
| `read` | `full` or `partial` |
| `verdict` | `clean`, `fix`, `drop` |
| `diseases` | the codes, separated by `;` (for example `A1;B3`) |
| `evidence` | the exact characters or a short quote, with the position (character offset) |
| `hex` | the hex dump of the bad characters, if the disease is in the A or G group |
| `note` | free text, at most one line |

Rules:
1. **`clean` means you read the whole document and found no disease.** It is a claim with your name on it.
2. A second reader reads 10% of your documents. We measure the agreement of the two readers.
3. For a language that you do not read well, do not judge D4 or D5. Mark the row `partial`.

## 4. The medicine sheet

For each disease that you find more than five times, propose one medicine. Use the template `medicine_<slice_id>.md`.

1. **The disease:** code, count, and three examples with `doc_id`.
2. **The medicine:** the rule, in words and in code (a regex or a short Python function).
3. **The action:** fix the text, or drop the document.
4. **The harm test:** run the medicine on the gold set of your language. Report the number of gold documents that
   it changes and the number that it drops. **A medicine that changes or drops more than 1% of the gold set fails.**
5. **The side effects:** the cases where the medicine is wrong.

## 5. The gold sets

A gold set is about 200 documents for each language and each code language that two readers marked `clean`. The
gold sets protect good text from bad medicine. The Data A and Data B teams own the gold sets.

## 6. What you give on each date

- **Tue 27 Oct:** the first 150 labelled rows, with evidence.
- **Sat 31 Oct:** all rows of your slice, and the medicine sheet with harm tests.
