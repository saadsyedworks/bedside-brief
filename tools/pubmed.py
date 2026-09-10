"""Thin, dependency-free NCBI e-utils / Crossref helper for extractors and red-team.

Usage (CLI):
  python tools/pubmed.py search "Does this patient have ascites[Title]"
  python tools/pubmed.py fetch 1573754            # title, journal, year, abstract
  python tools/pubmed.py pmc 1573754              # PMC id + OA full-text availability
  python tools/pubmed.py doi 10.1001/jama.1992.03480190087038
  python tools/pubmed.py grep 1573754 "likelihood"   # abstract lines containing a term
  python tools/pubmed.py fulltext 31110214 | grep -n "Table 2"   # PMC OA full text (PMID or PMCID); up to 200 kB
All calls honour HTTPS_PROXY. Never pass secrets here.
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from html import unescape

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
UA = {"User-Agent": "bedside-brief/0.1 (research; mailto:saadsyed14@gmail.com)"}
TOOL = "&tool=bedside_brief&email=saadsyed14%40gmail.com"


def _get(url: str, retries: int = 3) -> bytes:
    last = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(0.4 * (i + 1))
    raise RuntimeError(f"fetch failed: {url}: {last}")


def search(term: str, retmax: int = 10) -> list[str]:
    q = urllib.parse.quote(term)
    d = json.loads(_get(f"{EUTILS}esearch.fcgi?db=pubmed&term={q}&retmode=json&retmax={retmax}{TOOL}"))
    return d["esearchresult"].get("idlist", [])


def _tag(x: str, tag: str) -> str:
    m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", x, re.S)
    return unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""


def fetch(pmid: str) -> dict:
    x = _get(f"{EUTILS}efetch.fcgi?db=pubmed&id={pmid}&retmode=xml{TOOL}").decode("utf-8", "replace")
    abstract = " ".join(
        unescape(re.sub(r"<[^>]+>", "", m)).strip()
        for m in re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", x, re.S)
    )
    doi = ""
    m = re.search(r'<ArticleId IdType="doi">(.*?)</ArticleId>', x)
    if m:
        doi = m.group(1)
    authors = [
        (_tag(a, "LastName") + " " + _tag(a, "Initials")).strip()
        for a in re.findall(r"<Author[ >].*?</Author>", x, re.S)
    ]
    return {
        "pmid": pmid,
        "authors": [a for a in authors if a][:8],
        "title": _tag(x, "ArticleTitle"),
        "journal": _tag(x, "Title"),
        "year": _tag(x, "Year"),
        "doi": doi,
        "abstract": abstract,
    }


def pmc(pmid: str) -> dict:
    """PMID -> PMCID (if any). open_access is best-effort: True when efetch returns article body text."""
    d = json.loads(_get(f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={pmid}&format=json{TOOL}"))
    rec = (d.get("records") or [{}])[0]
    out = {"pmid": pmid, "pmcid": rec.get("pmcid"), "doi": rec.get("doi"), "open_access": False}
    if out["pmcid"]:
        try:
            out["open_access"] = len(pmc_fulltext(out["pmcid"])) > 5000
        except Exception:  # noqa: BLE001
            out["open_access"] = False
    return out


def pmc_fulltext(ident: str) -> str:
    """Full text (tags stripped) for a PMCID ('PMC123' or '123'); a bare PMID is converted first."""
    ident = str(ident).strip()
    if not ident.upper().startswith("PMC"):
        # PMIDs are 7-8 digits; PMC numeric ids overlap, so treat bare digits as PMID and convert.
        d = json.loads(_get(f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={ident}&format=json{TOOL}"))
        rec = (d.get("records") or [{}])[0]
        if not rec.get("pmcid"):
            return f"NO PMC FULL TEXT for PMID {ident} (not in PMC)."
        ident = rec["pmcid"]
    x = _get(f"{EUTILS}efetch.fcgi?db=pmc&id={ident.replace('PMC', '')}&retmode=xml{TOOL}").decode("utf-8", "replace")
    if "<body" not in x:
        return f"PMC record {ident} exists but has no open-access body text (abstract-only deposit)."
    return unescape(re.sub(r"<[^>]+>", " ", x))


def doi_lookup(doi: str) -> dict:
    d = json.loads(_get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"))["message"]
    return {
        "doi": doi,
        "title": (d.get("title") or [""])[0],
        "container": (d.get("container-title") or [""])[0],
        "year": (d.get("issued", {}).get("date-parts") or [[None]])[0][0],
        "type": d.get("type"),
    }


def grep(pmid: str, term: str) -> list[str]:
    ab = fetch(pmid)["abstract"]
    return [s.strip() for s in re.split(r"(?<=[.;])\s+", ab) if term.lower() in s.lower()]


if __name__ == "__main__":
    cmd, *args = sys.argv[1:] or ["help"]
    fn = {"search": search, "fetch": fetch, "pmc": pmc, "doi": doi_lookup, "grep": grep, "fulltext": pmc_fulltext}.get(cmd)
    if not fn:
        print(__doc__)
        sys.exit(1)
    out = fn(*args)
    print(json.dumps(out, indent=2) if not isinstance(out, str) else out[:200000])
