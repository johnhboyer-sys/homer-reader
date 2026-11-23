"""The guard on the committed Greek (corpus/greek/).

Two promises. The build needs nothing but these files for a work's TLG Greek,
so each such work has one and stage 1 never runs Diogenes. And the files hold
lines of Greek and nothing of the TLG's own: no beta code, no Diogenes XML.
The check (greek_lines.forbidden) has its planted failing cases in
test_greek_lines.py; here it runs over the files themselves, and says how
many it read. Below that, the same promise for every other tracked file: no
Diogenes export hides in the repo outside the files pinned by name.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

from homer_pipeline import extract, greek_lines, stage1_greek, stage1_tlg_iliad
from homer_pipeline.config import REPO_ROOT, Manifest

MANIFESTS = sorted(p.stem for p in (REPO_ROOT / "manifests").glob("*.yaml") if not p.stem.endswith("-public"))
WORKS = [w for w in MANIFESTS if Manifest.for_work(w).data["work"].get("greek_source_kind") == "tlg"]


def test_the_guard_has_something_to_guard():
    # A check that examined nothing has not passed.
    assert MANIFESTS == ["Iliad", "Odyssey"], MANIFESTS
    assert WORKS == ["Iliad"], WORKS


def test_the_folder_holds_one_file_per_work_and_nothing_else():
    have = sorted(p.name for p in greek_lines.CORPUS_DIR.iterdir())
    assert have == sorted(["README.md", *(f"{w}.tsv" for w in WORKS)])
    assert all(p.is_file() and not p.is_symlink() for p in greek_lines.CORPUS_DIR.iterdir())


def test_the_readme_is_short_and_holds_no_markup():
    # The one file here the character rule cannot cover: it is English prose.
    # This holds it to a page (no export fits in 4 KB) and to no XML; that its
    # words are what they should be is for whoever reviews a change to it.
    readme = (greek_lines.CORPUS_DIR / "README.md").read_text(encoding="utf-8")
    assert 500 < len(readme.encode("utf-8")) < 4096, "the README has grown; nothing but a short page belongs there"
    assert not re.search(r"<\?xml|<TEI|<div|<l[ >]|</|xmlns", readme)
    assert "TLG" not in readme and "Diogenes" not in readme


@pytest.mark.parametrize("work", WORKS)
def test_each_file_is_lines_of_greek_under_its_own_heading(work):
    manifest = Manifest.for_work(work)
    path = greek_lines.corpus_path(manifest)
    text = path.read_text(encoding="utf-8")
    assert greek_lines.forbidden(text) == []
    rows = greek_lines.parse_tsv(text, path.name)
    assert len(rows) >= 15_000, f"{work}: only {len(rows)} lines"
    head = text.split("\n")[:2]
    assert head == [f"# work: {work}", "# edition: " + " ".join(manifest.data["work"]["greek_edition"].split())]
    # The licence page names editions; these files do the same and never name
    # the disc the text was read from.
    assert "TLG" not in text and "Thesaurus Linguae" not in text and "Diogenes" not in text


def test_the_whole_corpus_was_read(capsys):
    files = lines = signs = books = 0
    for w in WORKS:
        rows = greek_lines.load(greek_lines.corpus_path(Manifest.for_work(w)))
        files += 1
        lines += len(rows)
        signs += sum(1 for r in rows if r.sigla)
        books += len({r.book for r in rows})
    with capsys.disabled():
        print(f"\ncorpus/greek guard: read {files} files, {lines} lines in {books} books, {signs} margins with signs")
    assert files == len(WORKS) and lines > 15_000 and books == 24 and signs > 2_500, (files, lines, books, signs)


def test_the_iliad_spine_is_the_one_the_build_has_always_made():
    # The spine stage 1 makes from the line file, pinned. It was proved byte
    # for byte the spine the old code made from the export (HANDOFF-PORTABILITY.md,
    # phase 1 record); a change to the file or to stage 1 that moves it fails here.
    m = Manifest.for_work("Iliad")
    spine = stage1_tlg_iliad.parse_rows(stage1_tlg_iliad.read_lines(m), m)
    body = json.dumps(spine, ensure_ascii=False, indent=1).encode("utf-8")
    assert (len(body), hashlib.sha256(body).hexdigest()) == (
        2075799, "de46221e5fe26876d10146727efd37460a8e3fa82a54b96c1bf91ceb7fd6e4b3"), "the Iliad's spine moved"


def test_stage_1_stops_on_a_missing_line_file_and_does_not_run_diogenes(tmp_path, monkeypatch):
    monkeypatch.setattr(greek_lines, "CORPUS_DIR", tmp_path)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("the build ran a program"))
    monkeypatch.setattr(stage1_tlg_iliad, "BUILD_DIR", tmp_path / "build")
    with pytest.raises(FileNotFoundError, match="homer_pipeline.extract --work Iliad"):
        stage1_tlg_iliad.run(Manifest.for_work("Iliad"))
    # and neither stage 1 module has a way to: the export call lives in extract alone
    for module in (stage1_tlg_iliad, stage1_greek):
        assert not hasattr(module, "subprocess") and not hasattr(module, "run_export"), module.__name__


def test_the_export_folder_cannot_be_committed():
    # extract writes the Diogenes XML under build/export; git must ignore it.
    r = subprocess.run(["git", "check-ignore", "-q", str(extract.EXPORT_DIR / "Diogenes-Resources" / "xml" / "tlg" / "tlg0012001.xml")],
                       cwd=REPO_ROOT)
    assert r.returncode == 0, "build/export is not git-ignored"
    tracked = subprocess.run(["git", "ls-files", "build", "*Diogenes-Resources*"], cwd=REPO_ROOT, capture_output=True, text=True)
    assert tracked.returncode == 0, tracked.stderr
    assert tracked.stdout == "", tracked.stdout[:400]
    # and git did answer: the same question about a folder it does track
    assert subprocess.run(["git", "ls-files", "manifests"], cwd=REPO_ROOT, capture_output=True, text=True).stdout


# ---- extract ---------------------------------------------------------------

def _export(tmp_path, lines: int, text: str = "λόγος"):
    xml = tmp_path / f"x{lines}.xml"
    xml.write_text('<TEI><body><div type="Book" n="1">'
                   + "".join(f'<l n="{n}">{text}</l>' for n in range(1, lines + 1)) + "</div></body></TEI>",
                   encoding="utf-8")
    return xml


def test_extract_skips_the_vendored_odyssey_and_never_exports_it(monkeypatch):
    monkeypatch.setattr(extract, "ensure_export", lambda m: pytest.fail("exported a vendored work"))
    assert extract.line_file(Manifest.for_work("Odyssey")) is None


def test_extract_refuses_to_write_a_file_the_guard_would_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(greek_lines, "CORPUS_DIR", tmp_path / "out")
    monkeypatch.setattr(extract, "ensure_export", lambda m: _export(tmp_path, 1, "mh=nin a)/eide qea/"))
    with pytest.raises(ValueError, match="refusing"):
        extract.main(["--work", "Iliad"])
    assert not (tmp_path / "out").exists()


def test_extract_will_not_replace_a_file_with_a_shorter_one_unless_told(tmp_path, monkeypatch):
    out = tmp_path / "out"
    monkeypatch.setattr(greek_lines, "CORPUS_DIR", out)
    monkeypatch.setattr(extract, "ensure_export", lambda m: _export(tmp_path, 3))
    assert extract.main(["--work", "Iliad"]) == 0
    full = (out / "Iliad.tsv").read_text(encoding="utf-8")
    # the export comes back cut short: well formed, and two lines gone
    monkeypatch.setattr(extract, "ensure_export", lambda m: _export(tmp_path, 1))
    assert extract.main(["--work", "Iliad"]) == 1
    assert (out / "Iliad.tsv").read_text(encoding="utf-8") == full
    assert extract.main(["--work", "Iliad", "--allow-fewer-lines"]) == 0
    assert len((out / "Iliad.tsv").read_text(encoding="utf-8").split("\n")) == 3 + 1 + 1


def test_extract_refuses_a_file_that_does_not_read_back(tmp_path, monkeypatch):
    # Break the file's reader alone (a sign lost on the way back) and it must stop.
    monkeypatch.setattr(greek_lines, "CORPUS_DIR", tmp_path / "out")
    monkeypatch.setattr(extract, "ensure_export", lambda m: _export(tmp_path, 3))
    real = greek_lines.parse_tsv
    monkeypatch.setattr(greek_lines, "parse_tsv",
                        lambda text, name="": [r._replace(sigla="—") if r.n == "2" else r for r in real(text, name)])
    with pytest.raises(ValueError, match="does not read back"):
        extract.main(["--work", "Iliad"])
    assert not (tmp_path / "out").exists()


# write_all is shared with Aristotle's and Plato's extract; Homer has one TLG
# work, so its tests stage made-up works W1 to W5 directly.
FAKE = [f"W{i}" for i in range(1, 6)]


def _made(tag: str):
    return [(Manifest({"work": {"id": w}}, Path(f"{w}.yaml")), f"# work: {w} {tag}\n", 1) for w in FAKE]


def _old_corpus(tmp_path, monkeypatch):
    out = tmp_path / "out"
    monkeypatch.setattr(greek_lines, "CORPUS_DIR", out)
    extract.write_all(_made("old"))
    return out, {p.name: p.read_text(encoding="utf-8") for p in out.iterdir()}


def _third_move_fails(monkeypatch):
    real, moves = Path.replace, []

    def replace(self, target):
        if self.suffix == ".tmp":                         # a move into place, not a put-back
            moves.append(self.name)
            if len(moves) == 3:
                raise PermissionError(1, "Operation not permitted", str(target))
        return real(self, target)
    monkeypatch.setattr(Path, "replace", replace)
    return moves


def test_a_write_that_fails_part_way_leaves_every_old_file_as_it_was(tmp_path, monkeypatch):
    out, before = _old_corpus(tmp_path, monkeypatch)
    (out / "W4.tsv.tmp").mkdir()                          # the disk refuses one of the later ones
    with pytest.raises(OSError):
        extract.write_all(_made("new"))
    (out / "W4.tsv.tmp").rmdir()
    assert {p.name: p.read_text(encoding="utf-8") for p in out.iterdir()} == before


def test_a_move_that_fails_part_way_puts_back_the_files_already_moved(tmp_path, monkeypatch):
    out, before = _old_corpus(tmp_path, monkeypatch)
    (out / "W1.tsv").unlink()                             # the first moved has no file yet
    before.pop("W1.tsv")
    moves = _third_move_fails(monkeypatch)
    with pytest.raises(PermissionError):
        extract.write_all(_made("new"))
    assert len(moves) == 3
    assert {p.name: p.read_text(encoding="utf-8") for p in out.iterdir()} == before


def test_a_write_that_fails_part_way_leaves_no_temporary_file(tmp_path, monkeypatch):
    out = tmp_path / "out"
    monkeypatch.setattr(greek_lines, "CORPUS_DIR", out)
    real, writes = Path.write_text, []

    def write_text(self, text, *a, **k):
        writes.append(self.name)
        if len(writes) == 2:
            real(self, text[:3], *a, **k)
            raise OSError(28, "No space left on device")
        return real(self, text, *a, **k)
    monkeypatch.setattr(Path, "write_text", write_text)
    with pytest.raises(OSError):
        extract.write_all(_made("new"))
    assert list(out.iterdir()) == []


def test_a_put_back_that_fails_names_its_file_and_the_others_are_still_put_back(tmp_path, monkeypatch, capsys):
    out, before = _old_corpus(tmp_path, monkeypatch)
    _third_move_fails(monkeypatch)
    real_write = Path.write_bytes

    def write_bytes(self, data):
        if self.name == "W1.tsv.back":
            real_write(self, data[:2])
            raise OSError(28, "No space left on device")
        return real_write(self, data)
    monkeypatch.setattr(Path, "write_bytes", write_bytes)
    with pytest.raises(PermissionError):
        extract.write_all(_made("new"))
    after = {p.name: p.read_text(encoding="utf-8") for p in out.iterdir()}
    assert "W1.tsv" in capsys.readouterr().err
    assert after["W1.tsv"] == "# work: W1 new\n"         # whole, not cut short
    assert {k: v for k, v in after.items() if k != "W1.tsv"} == {k: v for k, v in before.items() if k != "W1.tsv"}


def test_a_temp_that_cannot_be_removed_stops_no_put_back_and_hides_no_error(tmp_path, monkeypatch, capsys):
    out, before = _old_corpus(tmp_path, monkeypatch)
    _third_move_fails(monkeypatch)
    real_unlink = Path.unlink

    def unlink(self, missing_ok=False):
        if self.name == "W3.tsv.tmp":
            raise OSError(30, "Read-only file system", str(self))
        return real_unlink(self, missing_ok=missing_ok)
    monkeypatch.setattr(Path, "unlink", unlink)
    with pytest.raises(PermissionError) as caught:
        extract.write_all(_made("new"))
    assert caught.value.errno == 1
    assert "W3.tsv.tmp" in capsys.readouterr().err
    assert {p.name: p.read_text(encoding="utf-8") for p in out.iterdir() if p.suffix == ".tsv"} == before
    assert sorted(p.name for p in out.iterdir() if p.suffix != ".tsv") == ["W3.tsv.tmp"]


def test_a_back_file_that_cannot_be_removed_stops_no_later_put_back(tmp_path, monkeypatch, capsys):
    out, before = _old_corpus(tmp_path, monkeypatch)
    (out / "W1.tsv.back").mkdir()
    _third_move_fails(monkeypatch)
    with pytest.raises(PermissionError) as caught:
        extract.write_all(_made("new"))
    assert caught.value.errno == 1 and not str(caught.value.filename).endswith(".back")
    assert "W1.tsv" in capsys.readouterr().err
    assert (out / "W2.tsv").read_text(encoding="utf-8") == before["W2.tsv"]


# ---- export-shaped text outside corpus/greek/ (decision 10) ---------------
# A Diogenes export is known by its line elements (<l n="1">…</l>), the
# sentence its header opens with (EXPORT_HEADER), or its file name
# (tlg0012001.xml). The files allowed more than a few such lines are pinned
# below, by name, size and hash, each with its reason; any other tracked file
# may hold a handful (the tests' made-up Greek, a doc's example) and no header
# or export name.

# A line or line-break element with a number, in either quote: <l n="1">,
# <l rend="x" n='1a'>, <lb n="1"/>.
EXPORT_LINE = re.compile(r"""<lb?\b[^<>]*?\bn\s*=\s*["'][^"'<>]*["']""")
# Written with \s+ so that this file does not match itself.
EXPORT_HEADER = re.compile(r"generated\s+by\s+Diogenes|from\s+the\s+TLG\s+corpus")
EXPORT_NAME = re.compile(r"(^|/)tlg\d{7}\.xml$", re.I)
FEW = 30   # well under a book of the Iliad (the shortest runs to 424 lines)
# In all tracked files but the pinned ones together, so an export split small
# fails too: 51 today (the tests' made-up Greek, 26 of them in this file and
# test_greek_lines.py, and doc examples); 80 leaves room for a new test, and
# is a fifth of the shortest book.
ALL = 80
PINNED = {
    # Decision 10, open (John rules): two test fixtures in the export's markup.
    "pipeline/tests/fixtures/stephanus/euthyphro_p2_3.xml": {
        "bytes": 9369, "sha256": "38226581bfbb162fc7b8e67e375d954ba708cfb58fc240bd103543c3001420eb", "lines": 77,
        "why": "Plato's fixture, copied here; ruled A (kept, pinned) for plato-reader on 2026-11-21"},
    "pipeline/tests/fixtures/stage1_tlg/tiny_tlg_iliad.xml": {
        "bytes": 1601, "sha256": "6cf835c6e3e9036a1586d2d81d83c35101d0fdef8533f8625b8dfef550acc88d", "lines": 9,
        "why": "the export's markup round Il. 1.1-5 and Od. 1.1-4, with made-up signs"},
    # Not exports: Perseus's own TEI (CC BY-SA), the Greek the build reads
    # for the Odyssey and the four supplied lines of Il. 8. Pinned so an
    # export cannot pass under their names.
    "sources/perseus/tlg0012.tlg001.perseus-grc2.xml": {
        "bytes": 2060459, "sha256": "ebbdfdd7b6ebd52c4ecdfdb92c17cef4447ccbb5114f7fb00cd34f434dd8521b", "lines": 15687,
        "why": "Perseus TEI of the Iliad (Monro-Allen), not an export"},
    "sources/perseus/tlg0012.tlg002.perseus-grc2.xml": {
        "bytes": 1560139, "sha256": "184fa4fc598f0cd9d2964b17eaabe36bd9c61d44c2eae264c4b016feacf28530", "lines": 12107,
        "why": "Perseus TEI of the Odyssey (Murray's Loeb Greek), not an export"},
}


def _texts(body: bytes) -> list[str]:
    """The file read as UTF-8, and, when it holds a NUL, as UTF-16 both ways
    too: a UTF-16 copy reads as letters with NULs between them in UTF-8."""
    texts = [body.decode("utf-8", errors="ignore")]
    if b"\0" in body:
        texts += [body.decode(enc, errors="ignore") for enc in ("utf-16-le", "utf-16-be")]
    return texts


def export_problems(files: dict[str, bytes]) -> list[str]:
    """What a text scan can find. Out of its reach, by its method: a
    compressed, encrypted, or otherwise encoded copy, a submodule's files,
    and files git does not track. Beta code outside corpus/greek/ is not
    looked for: the pipeline keeps beta-code lookup keys of its own."""
    problems = []
    total = 0
    for path, body in sorted(files.items()):
        texts = _texts(body)
        lines = max(len(EXPORT_LINE.findall(t)) for t in texts)
        if EXPORT_NAME.search(path):
            problems.append(f"{path}: named like a Diogenes export")
        if any(EXPORT_HEADER.search(t) for t in texts):
            problems.append(f"{path}: holds a Diogenes export's header words")
        pin = PINNED.get(path)
        if pin:
            got = {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(), "lines": lines}
            if got != {k: pin[k] for k in got}:
                problems.append(f"{path}: the pinned file changed: {got}, pinned {pin}")
        else:
            total += lines
            if lines > FEW:
                problems.append(f"{path}: {lines} export lines, more than {FEW}; only a pinned file may hold more")
    if total > ALL:
        problems.append(f"{total} export lines in all tracked files but the pinned ones, more than {ALL}")
    for path in PINNED:
        if path not in files:
            problems.append(f"{path}: the pinned file is gone; take it off the list")
    return problems


def _tracked() -> dict[str, bytes]:
    names = subprocess.run(["git", "ls-files", "-z"], cwd=REPO_ROOT, capture_output=True, check=True).stdout.split(b"\0")
    out = {}
    for raw in filter(None, names):
        name = raw.decode("utf-8")
        p = REPO_ROOT / name
        if p.is_file() and not p.is_symlink():
            out[name] = p.read_bytes()
    return out


def _pinned() -> dict[str, bytes]:
    return {p: (REPO_ROOT / p).read_bytes() for p in PINNED}


_EXPORT = ('<?xml version="1.0"?>\n<TEI><text><body><div type="Book" n="1">\n'
           + "".join(f'<l n="{n}">λόγος</l>\n' for n in range(1, 41)) + "</div></body></text></TEI>\n")
FIX = "pipeline/tests/fixtures/stephanus/euthyphro_p2_3.xml"
TINY = "pipeline/tests/fixtures/stage1_tlg/tiny_tlg_iliad.xml"
PERSEUS = "sources/perseus/tlg0012.tlg001.perseus-grc2.xml"


@pytest.mark.parametrize("files, wanted", [
    ({"sources/x.xml": _EXPORT.encode()}, "40 export lines, more than 30"),
    ({"docs/notes.md": ("This XML text was generated " + "by Diogenes (version 4.7.2)").encode()}, "header words"),
    ({"docs/notes.md": ("from the TLG " + "corpus of classical texts").encode()}, "header words"),
    ({"sources/tlg0012001.xml": b"<TEI/>"}, "named like a Diogenes export"),
    ({"x/TLG0012002.XML": b""}, "named like a Diogenes export"),
    ({FIX: _EXPORT.encode()}, "the pinned file changed"),
    ({TINY: _EXPORT.encode()}, "the pinned file changed"),
    # the Iliad's export put in place of Perseus's file, under its name
    ({PERSEUS: _EXPORT.encode()}, "the pinned file changed"),
    ({"drop": FIX}, "the pinned file is gone"),
    ({"sources/x.xml": "".join(f"<l n='{n}'>λόγος</l>" for n in range(1, 41)).encode()}, "40 export lines"),
    ({"sources/x.xml": "".join(f'<l rend="x" n="{n}a">λόγος</l>' for n in range(1, 41)).encode()}, "40 export lines"),
    ({"sources/x.xml": "".join(f'<lb n="{n}"/>λόγος' for n in range(1, 41)).encode()}, "40 export lines"),
    ({"sources/x.xml": _EXPORT.encode("utf-16-le")}, "40 export lines"),
    ({"sources/x.xml": ("This XML text was generated " + "by Diogenes").encode("utf-16")}, "header words"),
    ({f"sources/part{i}.xml": "".join(f'<l n="{n}">λόγος</l>' for n in range(1, 21)).encode() for i in range(5)}, "export lines in all"),
    ({"same size": TINY}, "the pinned file changed"),
])
def test_export_shaped_text_outside_the_pins_fails(files, wanted):
    base = _pinned()
    if "drop" in files:
        base.pop(files.pop("drop"))
    if "same size" in files:
        # One letter for another of the same length: size and lines kept, the hash not.
        path = files.pop("same size")
        body = base[path]
        files[path] = body.replace("Μῆνιν".encode(), "Μῆνεν".encode(), 1)
        assert len(files[path]) == len(body) and files[path] != body
    assert any(wanted in p for p in export_problems({**base, **files})), export_problems({**base, **files})


def test_a_few_made_up_lines_pass():
    few = "".join(f'<l n="{n}">λόγος</l>' for n in range(1, FEW + 1)).encode()
    assert export_problems({"pipeline/tests/x.py": few, **_pinned()}) == []


def test_no_tracked_file_is_export_shaped_but_the_pinned_ones(capsys):
    files = _tracked()
    with_lines = {p: max(len(EXPORT_LINE.findall(t)) for t in _texts(b)) for p, b in files.items()}
    with_lines = {p: n for p, n in with_lines.items() if n}
    with capsys.disabled():
        print(f"\nexport-shape guard: read {len(files)} tracked files, {sum(len(b) for b in files.values())} bytes; "
              f"export lines in {len(with_lines)}: " + ", ".join(f"{p} {n}" for p, n in sorted(with_lines.items())))
    assert len(files) > 1000, len(files)          # git answered with the repo, not nothing
    assert export_problems(files) == []
