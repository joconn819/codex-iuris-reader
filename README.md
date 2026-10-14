# Codex Iuris — Latin & English

A browser-based parallel reader for all 1,752 canons of the 1983 Code of Canon Law, with a Latin concordance.

This website was vibe-coded using [Codex](https://openai.com/codex/).

## Run

```sh
npm start
```

Open http://localhost:8080. Python 3 serves the static files; there are no application dependencies or build step. Any static web host can serve `dist/`. The complete text and precomputed Latin analysis are bundled, so normal use never needs a model server or API key. Google Fonts is optional; local serif/sans-serif fallbacks work without it.

## Use

- Navigate among seven books or enter any canon number. Latin and English remain side by side and aligned by canon.
- Click a Latin word to see its predicted lemma, grouped inflections, frequency, and linked occurrences throughout the Code.
- Search a dictionary headword or attested inflected Latin form.
- Filter counts to a book, switch to exact spelling counts, or click a form within a lemma to narrow the concordance.
- Hover over words for part of speech and grammatical features.
- Export the full filtered frequency list or concordance as CSV.
- Reader position is stored only in the browser. Canon links use `#canon=123`.

## Text and linguistic provenance

Latin: https://www.vatican.va/archive/cod-iuris-canonici/cic_index_la.html

English: https://www.vatican.va/archive/cod-iuris-canonici/cic_index_en.html

The bundled corpus is a dated snapshot of those pages. It includes the revised Book VI as served by the Vatican. Different language pages may reflect amendments at different times; this is not a certified consolidated legal edition. The app includes per-canon source links. Text rights remain with their respective owners; no rights over source texts are asserted here.

Lemmatization: LatinCy `la_core_web_sm` 3.9.8, MIT licensed, https://huggingface.co/latincy/la_core_web_sm (revision `c433837a66f74643ba49bf853b87927954c7d701`). It uses context to assign one lemma to each Latin token. This groups conjugations and noun/adjective declensions, including irregular forms. It is **machine analysis, not a manually verified ecclesiastical Latin lexicon**. Ambiguous forms can be assigned different lemmas in different contexts. Unknown words may remain under their surface form or receive an incorrect prediction.

Counts exclude headings, canon labels, numbers, and punctuation. Enclitics may be split by LatinCy; capitalization and macrons are ignored and j becomes i. Exact-form counts aggregate identical normalized spellings across predicted lemmas. Frequency scope is always explicit. CSV rows represent individual occurrences, even where a canon contains a word more than once.

## Regenerate data

Requires Python 3.12, `requests`, `beautifulsoup4`, and the LatinCy model and its dependencies. Download the wheel named `la_core_web_sm-3.9.8-py3-none-any.whl` from the pinned model revision above, then:

```sh
python3.12 -m venv .nlp
.nlp/bin/pip install requests beautifulsoup4 /path/to/la_core_web_sm-3.9.8-py3-none-any.whl
.nlp/bin/python scripts/build_corpus.py
npm test
```

The importer caches source HTML in `.cache/`; remove that directory before deliberately refreshing source texts. It fails if either language is missing a canon or includes duplicates. It handles Book VI's table layout and the two Latin canons combined in one source paragraph at 1666–1667. The generated JSON includes token offsets, lemmas, parts of speech, morphology, and source URLs. Tests validate coverage, offset integrity, irregular grouping, concordance/count consistency, scope filters, exact-form counting, and source boundary cases.

## Files

- `dist/index.html`, `styles.css`, `app.js`: accessible responsive interface.
- `dist/engine.js`: indexing, lookup, filtering, and CSV serialization.
- `dist/data/corpus.json`: complete aligned texts and contextual linguistic annotations.
- `dist/data/latin-glosses.json`: concise English dictionary glosses keyed by normalized Latin lemma.
- `scripts/build_corpus.py`: reproducible data ingestion and preprocessing.
- `scripts/build_english_glosses.py`: builds the static English glossary from the pinned LatinCy lexicon package.
- `tests/engine.test.mjs`: data and concordance integrity tests.

### Editorial handling

The importer keeps the first main-text occurrence of each canon on a page and excludes repeated historical versions and bracketed amendment citations from the word counts. It retains source wording and typographical errors. Common ecclesiastical noun forms receive explicit corrections from `scripts/lemma_overrides.json`; these improve lemma grouping without claiming a full manual review. Morphological features remain model predictions.

The Vatican English pages contain Latin amendments in canons 111, 112, and 868. This reader supplies its own clearly labeled English study translations for these three canons in `scripts/english_supplements.json`, based on the imported Latin. These are not an official translation. Other English pages may lag behind amendments in the Latin; verify the linked sources for legal use.

## GitHub Pages

The live site is published from `dist/` using the workflow in `.github/workflows/pages.yml`. Push changes to `dist/` on `main` to publish an update. The GitHub Pages address is `https://joconn819.github.io/codex-iuris-reader/`.

GitHub Pages requires a public repository for accounts on the GitHub Free plan. The bundled Code texts and source files in this repository are therefore publicly visible. See Sources & method in the reader and the source links for text provenance and translation notes.

## English glosses

The focused overrides are recorded in `scripts/english_gloss_overrides.json`. To regenerate the glossary after rebuilding the corpus, install `scripts/gloss-requirements.txt` and run `python3 scripts/build_english_glosses.py`.

The frequency lists show concise English glosses for Latin headwords; exact-spelling counts use the glosses of their predicted lemma or lemmas. They combine dictionary data with focused gloss overrides for common legal and grammatical terms. Where no gloss is available, the list links to the English canon context. These glosses are not context-selected translations, so a gloss may not fit every occurrence. The dictionary data is derived from [Whitaker’s Words](https://mk270.github.io/whitakers-words/) and [Lewis & Short](https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.04.0059), packaged through [LatinCy’s lexicon project](https://github.com/latincy/latincy-lexicon). Whitaker’s data is freely reusable and asks that its source be credited; Lewis & Short was published in 1879 and the digitized source is provided by the Perseus Digital Library.

## Latin word index

Open the [live Latin word index](https://joconn819.github.io/codex-iuris-reader/words.html) to browse words in frequency order, search the Latin word list, scope counts to a book, switch between grouped lemmas and exact spellings, sort alphabetically, and export filtered results as CSV. Selecting a row opens the parallel reader at the word’s canon contexts.
