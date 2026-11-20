"""Run the upstream intake on the unmodified B PDF, including its WPS math glyphs.

The glyph transcription below was checked against rendered pages 1, 2 and 5.
It applies after upstream detection and before upstream UTF-8 hashing.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys


PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parent
PIPELINE = WORKSPACE / "工具" / "Multi-agent-mathematical-modeling" / "pipeline"
SOURCE_SHA256 = "9585081e724cef939d4e5713ea72f9eddefd4469a3b519a8ce184677d407692a"
MISSING_GLYPH = "\ud835"


def transcribe_math(text: str) -> str:
    if MISSING_GLYPH not in text:
        return text
    # @ marks the one broken UTF-16 code unit in each affected glyph.
    fragments = (
        ("situated at @ =(50,50)", "situated at O =(50,50)"),
        ("denoted as ( @ , @ , @ )", "denoted as (θ, R, H)"),
        ("Here, @ stands for the azimuth", "Here, θ stands for the azimuth"),
        ("@ denotes the horizontal distance", "R denotes the horizontal distance"),
        ("@ represents the target altitude", "H represents the target altitude"),
        ("( @ @ , @ @ )=(50+ @ cos @ , 50+ @ sin @ )",
         "(T_x, T_y) = (50 + R cos θ, 50 + R sin θ)"),
        ("three-dimensional position is @ =( @ @ , @ @ , @ )",
         "three-dimensional position is T = (T_x, T_y, H)"),
        ("completion ratio @ = @ @", "completion ratio η = k/N"),
    )
    for damaged, verified in fragments:
        original = damaged.replace("@", MISSING_GLYPH)
        if text.count(original) != 1:
            raise ValueError(f"Unexpected PDF extraction near {verified!r}.")
        text = text.replace(original, verified)
    text.encode("utf-8")
    return text


def main() -> None:
    sources = [
        pdf
        for folder in WORKSPACE.glob("*赛题")
        for pdf in folder.rglob("*B_Problem.pdf")
    ]
    if len(sources) != 1:
        raise ValueError("Expected one official B problem PDF.")
    pdf = sources[0]
    if hashlib.sha256(pdf.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("The official input has changed. Recheck the page transcription.")

    poppler = shutil.which("pdftotext")
    if poppler is None:
        git = shutil.which("git")
        if git:
            portable_bin = Path(git).parent.parent / "mingw64" / "bin"
            if (portable_bin / "pdftotext.exe").is_file():
                os.environ["PATH"] = str(portable_bin) + os.pathsep + os.environ.get("PATH", "")
            poppler = shutil.which("pdftotext")
    if poppler:
        other_text = subprocess.check_output([poppler, "-layout", "-enc", "UTF-8", str(pdf), "-"])
        if b"Rescheduling and Scheme Comparison" not in other_text:
            raise ValueError("The independent text read did not reach Problem 4.")
    else:
        print("Optional Poppler cross-check unavailable in this environment.")

    sys.path.insert(0, str(PIPELINE))
    from ingest import anti_poison_gate
    from orchestrator import Orchestrator

    scan_original = anti_poison_gate.scan_one

    def scan_with_transcription(*args, **kwargs):
        scan = scan_original(*args, **kwargs)
        if scan["kind_class"] != "pdf" or not scan.get("clean_text"):
            raise ValueError("The upstream detector did not return the PDF text.")
        # Findings, their severities, the source hash and the raw channel are preserved.
        scan["clean_text"] = transcribe_math(scan["clean_text"])
        return scan

    anti_poison_gate.scan_one = scan_with_transcription
    try:
        result = Orchestrator(None).s_1_ingest_gate(
            [pdf], outdir=str(PROJECT / "stage_S-1_ingest"), strict=True
        )
    finally:
        anti_poison_gate.scan_one = scan_original
    print(result["status"], result["severity_counts"], len(result["clean_text"]))


if __name__ == "__main__":
    main()
