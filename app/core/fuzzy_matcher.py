from typing import Dict, List, Tuple, Any
import re
import difflib

try:
    from rapidfuzz import fuzz, process
    USE_RAPIDFUZZ = True

except:
    USE_RAPIDFUZZ = False


STOPWORDS = {
    "a","an","and","or","the","is","in","of","to","for","on","by","with","at","from","as","it","we","you","they","he","she"
}



Word = str

def normalize(s: str) -> str:
    # lowercase, trim, collapse whitespace, strip punctuation except common separators

    s2 = re.sub(r"\s+", " ", s.lower().strip())
    s2 = re.sub(r"[^-\w\s&./']", "", s2)
    return s2

def smart_case(replacement: str, original: str) -> str:
    if original.isupper():
        return replacement.upper()
    
    if original.istitle():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def best_fuzzy(token: str, canon_keys: List[str], threshold: float) -> Tuple[str, float]:
    if not canon_keys:
        return (None, 0.0)
    
    if not USE_RAPIDFUZZ:
        import difflib
        def ratio(a,b):
            return difflib.SequenceMatcher(None, a, b).ratio() * 100
        best, score = None, 0.0
        for k in canon_keys:
            r = ratio(token, k)
            if r > score:
                best, score = k, r
        return (best, score) if score >= threshold else (None, score)
    
    best = process.extractOne(token, canon_keys, scorer=getattr(fuzz, "WRatio", fuzz.partial_ratio))
    if best is None:
        return (None, 0.0)
    cand, score, _ = best
    return (cand, score) if score >= threshold else (None, score)


def build_canonicals(metadata: Dict[str, Any]) -> Dict[str, str]:
    """
    Accepts a metadata dict like:
      {"people":[...], "companies":[...], "locations":[...], "frameworks":[...]}
    Values may be a string or a list of strings.
    Returns a dict: normalized_string -> original_canonical
    """
    pool: List[str] = []
    for _, v in (metadata or {}).items():
        if isinstance(v, str) and v.strip():
            pool.append(v)
        elif isinstance(v, (list, tuple)):
            for item in v:
                if isinstance(item, str) and item.strip():
                    pool.append(item)
    # de-duplicate by normalized form (last one wins if collisions)
    canon: Dict[str, str] = {}
    for val in pool:
        canon[normalize(val)] = val
    return canon


def correct_transcript_segment(segment: Dict[str, Any],
                               metadata: Dict[str, Any],
                               add_terminal_period: bool = False,
                               threshold: float = 80.0
                            ) -> Dict[str, Any]:
    
    """
    Token level matching against metadata strings.
    """

    canon = build_canonicals(metadata)
    keys = list(canon.keys())

    text = segment.get("text", "")
    tokens = re.findall(r"\w+|\s+|[^\w\s]", text, re.UNICODE)
    out: List[str] = []
    changes: List[Dict[str, Any]] = []

    for t in tokens:
        if not re.match(r"\w+", t):
            out.append(t)
            continue
        tn = normalize(t)

        # Skip smol short tokens and common words :3

        if len(tn) < 3 or tn in STOPWORDS:
            out.append(t)
            continue

        cand_key, score = best_fuzzy(tn, keys, threshold)

        if cand_key:
            raw_representation = canon[cand_key]
            rep = smart_case(raw_representation, t)

            if rep != t:
                out.append(rep)
                changes.append({"from": t, "to": rep, "reason": f"fuzzy:{int(score)}"})
            else:
                out.append(t)
        
        else:
            out.append(t)

    new = "".join(out)
    new = re.sub(r"\s+([.,?!])", r"\1", new)

    if add_terminal_period and new and new[-1].isalnum():
        new += "."
    
    out = dict(segment)
    out["text"] = new
    out["_stage1_changes"] = changes
    return out

