#!/usr/bin/env python3
"""Build the static English gloss lookup from Whitaker's Words lexicon data."""
import json
from pathlib import Path

from latincy_lexicon.align.normalize import normalize_latin
from latincy_lexicon.build import build_lexicon

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "dist/data/corpus.json"
OVERRIDES = ROOT / "scripts/english_gloss_overrides.json"
OUTPUT = ROOT / "dist/data/latin-glosses.json"


def main():
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    lexicon = build_lexicon()
    used_lemmas = {token[2] for canon in corpus["canons"] for token in canon["tokens"]}
    glosses = {}
    for lemma in sorted(used_lemmas):
        key = normalize_latin(lemma)
        matches = []
        for entry in lexicon.get(key, []):
            for gloss in entry.get("glosses", []):
                gloss = " ".join(gloss.split())
                if gloss and gloss not in matches:
                    matches.append(gloss)
        if matches:
            glosses[key] = "; ".join(matches[:4])

    glosses.update(json.loads(OVERRIDES.read_text(encoding="utf-8")))
    data = {
        "_meta": {
            "source": "Whitaker's Words and Lewis & Short, via LatinCy latincy-lexicon 0.13.0, with focused English gloss overrides",
            "coverage": "Dictionary senses are not context-selected; unmatched words link to their English canon context.",
        },
        **glosses,
    }
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Wrote {len(glosses):,} gloss entries to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
