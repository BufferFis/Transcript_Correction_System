# scripts/evaluate_pipeline.py
# Requires: pip install requests
import os
import time
import csv
import json
import re
from typing import Any, Dict, List
import requests

BASE_URL = os.getenv("PIPELINE_BASE_URL", "http://127.0.0.1:8000")
URL = BASE_URL.rstrip("/") + "/run"
OUT_CSV = os.getenv("EVAL_OUT_CSV", "./eval_results.csv")

# ---------------------------
# Readability helpers (FRE, FKGL + ARI, CLI, Fog, SMOG, Dale–Chall, LIX)
# ---------------------------

SENT_SPLIT = re.compile(r"[.!?]+")
WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
LETTER_RE = re.compile(r"[A-Za-z]")
ALNUM_RE = re.compile(r"[A-Za-z0-9]")

VOWELS = "aeiouy"

def count_sentences(text: str) -> int:
    parts = [p for p in SENT_SPLIT.split(text) if p.strip()]
    return max(1, len(parts))

def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))

def count_letters(text: str) -> int:
    return len(LETTER_RE.findall(text))

def count_alnum_chars(text: str) -> int:
    return len(ALNUM_RE.findall(text))

def count_long_words_letters(text: str, min_len: int = 7) -> int:
    return sum(1 for w in WORD_RE.findall(text) if len(w) >= min_len)

def count_syllables_in_word(word: str) -> int:
    w = word.lower()
    if w.endswith("e"):
        w = w[:-1]
    groups = 0
    prev = False
    for ch in w:
        is_vowel = ch in VOWELS
        if is_vowel and not prev:
            groups += 1
        prev = is_vowel
    return max(1, groups)

def count_syllables(text: str) -> int:
    return sum(count_syllables_in_word(w) for w in WORD_RE.findall(text))

def count_polysyllables(text: str, min_syllables: int = 3) -> int:
    return sum(1 for w in WORD_RE.findall(text) if count_syllables_in_word(w) >= min_syllables)

def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0

# Flesch Reading Ease (higher = easier)
def flesch_reading_ease(text: str) -> float:
    sentences = count_sentences(text)
    words = count_words(text)
    syllables = count_syllables(text)
    if words == 0:
        return 0.0
    return 206.835 - 1.015 * safe_div(words, sentences) - 84.6 * safe_div(syllables, words)

# Flesch–Kincaid Grade Level (lower = easier)
def fk_grade_level(text: str) -> float:
    sentences = count_sentences(text)
    words = count_words(text)
    syllables = count_syllables(text)
    if words == 0:
        return 0.0
    return 0.39 * safe_div(words, sentences) + 11.8 * safe_div(syllables, words) - 15.59

# Automated Readability Index (lower = easier)
def ari(text: str) -> float:
    sentences = count_sentences(text)
    words = count_words(text)
    chars = count_alnum_chars(text)  # ARI uses letters+numbers
    if words == 0:
        return 0.0
    return 4.71 * safe_div(chars, words) + 0.5 * safe_div(words, sentences) - 21.43

# Coleman–Liau Index (lower = easier)
def coleman_liau(text: str) -> float:
    words = count_words(text)
    sentences = count_sentences(text)
    letters = count_letters(text)  # CLI uses letters per 100 words
    if words == 0:
        return 0.0
    L = safe_div(letters, words) * 100.0
    S = safe_div(sentences, words) * 100.0
    return 0.0588 * L - 0.296 * S - 15.8

# Gunning Fog Index (lower = easier)
def gunning_fog(text: str) -> float:
    words = count_words(text)
    sentences = count_sentences(text)
    complex_words = count_polysyllables(text, min_syllables=3)
    if words == 0:
        return 0.0
    asl = safe_div(words, sentences)
    pcw = safe_div(complex_words, words) * 100.0
    return 0.4 * (asl + pcw)

# SMOG (lower = easier); adjusted for arbitrary sentence counts
def smog(text: str) -> float:
    sentences = count_sentences(text)
    polys = count_polysyllables(text, min_syllables=3)
    if sentences == 0:
        return 0.0
    # 1.043 * sqrt(polysyllables * (30/sentences)) + 3.1291
    import math
    return 1.043 * math.sqrt(polys * (30.0 / sentences)) + 3.1291

# Dale–Chall (approximate): use % polysyllabic words as “difficult”
def dale_chall_approx(text: str) -> float:
    words = count_words(text)
    sentences = count_sentences(text)
    if words == 0:
        return 0.0
    difficult = count_polysyllables(text, min_syllables=3)
    pdw = safe_div(difficult, words) * 100.0
    asl = safe_div(words, sentences)
    # 0.1579*PDW + 0.0496*ASL (+ 3.6365 if PDW > 5%)
    raw = 0.1579 * pdw + 0.0496 * asl
    if pdw > 5.0:
        raw += 3.6365
    return raw

# LIX (higher = harder): words/sentences + (100*long_words)/words, long words >= 7 letters
def lix(text: str) -> float:
    words = count_words(text)
    sentences = count_sentences(text)
    long_words = count_long_words_letters(text, min_len=7)
    if words == 0:
        return 0.0
    return safe_div(words, sentences) + (100.0 * safe_div(long_words, words))

# ---------------------------
# Examples (4 provided + 5 additional)
# ---------------------------

EXAMPLES: List[Dict[str, Any]] = [
    {
        "name": "Example 1: Entity Correction",
        "transcript": [
            {
                "end_timestamp": 49.5, "is_seller": False, "language": None,
                "speaker": "Anubhav Singh", "speaker_id": 100, "start_timestamp": 44,
                "text": "Hello. Hello. Thank you. Am I audible? Hi, Mohit."
            },
            {
                "end_timestamp": 69.5, "is_seller": True, "language": None,
                "speaker": "Rohit Agarwal", "speaker_id": 200, "start_timestamp": 50,
                "text": "Bank of America is in America."
            },
            {
                "end_timestamp": 73.5, "is_seller": False, "language": None,
                "speaker": "Anubhav Singh", "speaker_id": 100, "start_timestamp": 70,
                "text": "Pepsi is the organization we are working in. It is located in Bengu"
            }
        ],
        "metadata": {
            "people": ["Rohit"],
            "companies": ["Pepsales"],
            "locations": ["Bengaluru"],
            "frameworks": ["BANT"]
        }
    },
    {
        "name": "Example 2: Grammar and Punctuation",
        "transcript": [
            {
                "end_timestamp": 120.5, "is_seller": False, "language": None,
                "speaker": "Client Name", "speaker_id": 300, "start_timestamp": 115,
                "text": "um so like our budget is around you know fifty thousand and we need this by next quarter i think"
            }
        ],
        "metadata": {
            "people": ["Sarah"],
            "companies": ["TechCorp"],
            "locations": ["Mumbai"],
            "frameworks": ["MEDDIC"]
        }
    },
    {
        "name": "Example 3: Location and Company",
        "transcript": [
            {
                "end_timestamp": 95.5, "is_seller": False, "language": None,
                "speaker": "Prospect", "speaker_id": 500, "start_timestamp": 88,
                "text": "We at Micro Soft have offices in Bangalore and chen nai"
            }
        ],
        "metadata": {
            "people": ["John"],
            "companies": ["Microsoft"],
            "locations": ["Bengaluru", "Chennai"],
            "frameworks": ["BANT"]
        }
    },
    {
        "name": "Example 4: Multiple Corrections",
        "transcript": [
            {
                "end_timestamp": 210.5, "is_seller": True, "language": None,
                "speaker": "Sales Person", "speaker_id": 600, "start_timestamp": 200,
                "text": "so um Dave from amazon web services based in hyd mentioned that they need SAAS solution by Q1"
            }
        ],
        "metadata": {
            "people": ["David"],
            "companies": ["AWS"],
            "locations": ["Hyderabad"],
            "frameworks": ["MEDDIC"]
        }
    },
    {
        "name": "Example 5: Person Normalization",
        "transcript": [
            {
                "end_timestamp": 30.0, "is_seller": False, "language": None,
                "speaker": "Caller", "speaker_id": 101, "start_timestamp": 25.0,
                "text": "Spoke with Jon about the integration timeline"
            }
        ],
        "metadata": {"people": ["John"], "companies": [], "locations": [], "frameworks": []}
    },
    {
        "name": "Example 6: Company Canonical",
        "transcript": [
            {
                "end_timestamp": 52.3, "is_seller": True, "language": None,
                "speaker": "AE", "speaker_id": 42, "start_timestamp": 48.1,
                "text": "we use micro soft azure and aws for workloads"
            }
        ],
        "metadata": {"people": [], "companies": ["Microsoft", "AWS"], "locations": [], "frameworks": []}
    },
    {
        "name": "Example 7: Punctuation Cleanup",
        "transcript": [
            {
                "end_timestamp": 18.0, "is_seller": False, "language": None,
                "speaker": "SE", "speaker_id": 77, "start_timestamp": 10.0,
                "text": "Yes yes thank you we can start now"
            }
        ],
        "metadata": {"people": [], "companies": [], "locations": [], "frameworks": []}
    },
    {
        "name": "Example 8: Location Canonical",
        "transcript": [
            {
                "end_timestamp": 61.0, "is_seller": True, "language": None,
                "speaker": "Rep", "speaker_id": 88, "start_timestamp": 55.0,
                "text": "our delivery teams are in blr and hyd"
            }
        ],
        "metadata": {"people": [], "companies": [], "locations": ["Bengaluru", "Hyderabad"], "frameworks": []}
    },
    {
        "name": "Example 9: Filler Removal + Case",
        "transcript": [
            {
                "end_timestamp": 42.0, "is_seller": False, "language": None,
                "speaker": "Analyst", "speaker_id": 303, "start_timestamp": 37.0,
                "text": "uh like the SaaS platform needs an SSO integration you know"
            }
        ],
        "metadata": {"people": [], "companies": [], "locations": [], "frameworks": []}
    }
]

def post_run(transcript: List[Dict[str, Any]], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    resp = requests.post(URL, json={"transcript": transcript, "metadata": metadata}, timeout=120)
    resp.raise_for_status()
    return resp.json()

def evaluate() -> None:
    os.makedirs(os.path.dirname(OUT_CSV) or ".", exist_ok=True)
    # Expanded CSV header
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "example", "segment_index",
            "before_text", "after_text",
            # FRE/FKGL
            "fre_before", "fkgl_before", "fre_after", "fkgl_after", "delta_fre", "delta_fkgl",
            # ARI/CLI
            "ari_before", "cli_before", "ari_after", "cli_after", "delta_ari", "delta_cli",
            # Fog/SMOG
            "fog_before", "smog_before", "fog_after", "smog_after", "delta_fog", "delta_smog",
            # Dale–Chall (approx)
            "dale_before", "dale_after", "delta_dale",
            # LIX
            "lix_before", "lix_after", "delta_lix",
            # Timing
            "duration_ms_per_segment"
        ])

    total_segments = 0
    durations_ms: List[float] = []
    # For mean deltas
    acc_deltas: Dict[str, List[float]] = {
        "fre": [], "fkgl": [], "ari": [], "cli": [], "fog": [], "smog": [], "dale": [], "lix": []
    }

    for ex in EXAMPLES:
        before_texts = [seg["text"] for seg in ex["transcript"]]
        start = time.perf_counter()
        result = post_run(ex["transcript"], ex["metadata"])
        elapsed = (time.perf_counter() - start) * 1000.0
        per_seg_ms = elapsed / max(1, len(result))

        with open(OUT_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for i, seg in enumerate(result):
                before = before_texts[i]
                after = seg["text"]

                # Before metrics
                fre_b = flesch_reading_ease(before)
                fk_b = fk_grade_level(before)
                ari_b = ari(before)
                cli_b = coleman_liau(before)
                fog_b = gunning_fog(before)
                smog_b = smog(before)
                dale_b = dale_chall_approx(before)
                lix_b = lix(before)

                # After metrics
                fre_a = flesch_reading_ease(after)
                fk_a = fk_grade_level(after)
                ari_a = ari(after)
                cli_a = coleman_liau(after)
                fog_a = gunning_fog(after)
                smog_a = smog(after)
                dale_a = dale_chall_approx(after)
                lix_a = lix(after)

                # Deltas (after - before); note: for FKGL/Fog/SMOG/Dale/LIX lower is easier
                d_fre = fre_a - fre_b
                d_fk = fk_a - fk_b
                d_ari = ari_a - ari_b
                d_cli = cli_a - cli_b
                d_fog = fog_a - fog_b
                d_smg = smog_a - smog_b
                d_dal = dale_a - dale_b
                d_lix = lix_a - lix_b

                writer.writerow([
                    ex["name"], i,
                    before, after,
                    f"{fre_b:.2f}", f"{fk_b:.2f}", f"{fre_a:.2f}", f"{fk_a:.2f}", f"{d_fre:.2f}", f"{d_fk:.2f}",
                    f"{ari_b:.2f}", f"{cli_b:.2f}", f"{ari_a:.2f}", f"{cli_a:.2f}", f"{d_ari:.2f}", f"{d_cli:.2f}",
                    f"{fog_b:.2f}", f"{smog_b:.2f}", f"{fog_a:.2f}", f"{smog_a:.2f}", f"{d_fog:.2f}", f"{d_smg:.2f}",
                    f"{dale_b:.2f}", f"{dale_a:.2f}", f"{d_dal:.2f}",
                    f"{lix_b:.2f}", f"{lix_a:.2f}", f"{d_lix:.2f}",
                    f"{per_seg_ms:.2f}"
                ])

                total_segments += 1
                durations_ms.append(per_seg_ms)
                acc_deltas["fre"].append(d_fre)
                acc_deltas["fkgl"].append(d_fk)
                acc_deltas["ari"].append(d_ari)
                acc_deltas["cli"].append(d_cli)
                acc_deltas["fog"].append(d_fog)
                acc_deltas["smog"].append(d_smg)
                acc_deltas["dale"].append(d_dal)
                acc_deltas["lix"].append(d_lix)

    def mean(vals: List[float]) -> float:
        return sum(vals) / max(1, len(vals))

    summary = {
        "total_segments": total_segments,
        "avg_ms_per_segment": round(mean(durations_ms), 2),
        "mean_delta_fre": round(mean(acc_deltas["fre"]), 2),
        "mean_delta_fkgl": round(mean(acc_deltas["fkgl"]), 2),
        "mean_delta_ari": round(mean(acc_deltas["ari"]), 2),
        "mean_delta_cli": round(mean(acc_deltas["cli"]), 2),
        "mean_delta_fog": round(mean(acc_deltas["fog"]), 2),
        "mean_delta_smog": round(mean(acc_deltas["smog"]), 2),
        "mean_delta_dale": round(mean(acc_deltas["dale"]), 2),
        "mean_delta_lix": round(mean(acc_deltas["lix"]), 2),
        "csv": os.path.abspath(OUT_CSV),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    print(f"POST {URL}")
    evaluate()
