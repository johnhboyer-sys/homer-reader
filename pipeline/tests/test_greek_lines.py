"""The committed line files' format (homer_pipeline.greek_lines).

The failing cases come first: what the reader and the writer must refuse, and
what the check for markup and beta code must catch. Then the claim the build
rests on: a line file gives stage 1 the same spine as the XML it was made
from, sigla, obelos, bullet, "605*" and all. The Greek in these cases is the
opening of the Iliad or made up.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from homer_pipeline import greek_lines as gl
from homer_pipeline import stage1_tlg_iliad as s1
from homer_pipeline.config import Manifest

TEI = '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>{}</body></text></TEI>'


def _xml(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "t.xml"
    path.write_text(TEI.format(body), encoding="utf-8")
    return path


def _book(n: str, lines: str) -> str:
    return f'<div type="Book" n="{n}">{lines}</div>'


# ---- what rows_from_xml refuses -------------------------------------------

def test_a_book_inside_a_book_is_refused(tmp_path):
    with pytest.raises(ValueError, match="inside another book"):
        gl.rows_from_xml(_xml(tmp_path, _book("1", _book("2", '<l n="1">α</l>'))))


def test_a_book_number_twice_is_refused(tmp_path):
    # The old reader kept the first and dropped the second without a word.
    with pytest.raises(ValueError, match="book 1 twice"):
        gl.rows_from_xml(_xml(tmp_path, _book("1", '<l n="1">α</l>') + _book("1", '<l n="2">β</l>')))


@pytest.mark.parametrize("line", ['<l>α</l>', '<l n="">α</l>'])
def test_a_line_with_no_number_is_refused(tmp_path, line):
    # The old reader counted it under "(none)" and dropped it; none is attested.
    with pytest.raises(ValueError, match="no number"):
        gl.rows_from_xml(_xml(tmp_path, _book("1", line)))


def test_a_file_with_no_body_is_refused(tmp_path):
    path = tmp_path / "t.xml"
    path.write_text("<TEI><text/></TEI>", encoding="utf-8")
    with pytest.raises(ValueError, match="no TEI body"):
        gl.rows_from_xml(path)


# ---- what the writer and the reader refuse ---------------------------------

@pytest.mark.parametrize("row", [
    gl.Row("1", "1", "", "α\tβ"),            # a tab would shift the fields
    gl.Row("1", "1", "", "α\nβ"),            # a line break would make two lines
    gl.Row("1", "1", "—\t>", "α"),
    gl.Row("1\t2", "1", "", "α"),
    gl.Row("1", "1", "", "α  β"),            # not flat: would not read back the same
    gl.Row("1", "1", "> ", "α"),
])
def test_format_refuses_what_would_not_read_back(row):
    with pytest.raises(ValueError):
        gl.format_tsv([row], "T", "an edition")


H = "# work: T\n# edition: e\n# columns: book\tn\tsigla\ttext\n"


@pytest.mark.parametrize("text, message", [
    ("# work: T\n# edition: e\n# columns: Stephanus-page\tsection\tn\ttext\n2\ta\t1\tα\n", "expected # work"),
    ("# work: T\n1\t1\t\tα\n", "expected # work"),                                   # no columns line
    # a fourth heading line is a place to keep anything
    ("# work: T\n# edition: e\n# note: x\n# columns: book\tn\tsigla\ttext\n1\t1\t\tα\n", "expected # work"),
    ("# edition: e\n# work: T\n# columns: book\tn\tsigla\ttext\n1\t1\t\tα\n", "expected # work"),
    # ... and so is a "# " line among the lines of text: it is not skipped
    (H + "# mh=nin\n1\t1\t\tα\n", "tab-separated fields"),
    (H + "1\t1\tα\n", "tab-separated fields"),
    (H + "1\t1\t\tα\tβ\n", "tab-separated fields"),
    (H + "\t1\t\tα\n", "empty book"),
    (H + "1\t\t\tα\n", "empty book"),
    (H + "1\t1\t\tα\r\n", "tab-separated fields"),
    (H, "no lines of text"),     # examined nothing
    ("", "expected # work"),
])
def test_parse_refuses_a_file_of_the_wrong_shape(text, message):
    with pytest.raises(ValueError, match=message):
        gl.parse_tsv(text)


# ---- the check for markup, beta code, and bytes that are not text ----------

# A title line with no text, a line with the diplē and a correction, the
# export's ano teleia (U+0387) and question mark (U+037E), an elision, the
# bullet, and the starred number.
CLEAN = (H + "1\tt\t\t\n"
         "1\t1\t> corr.\tΜῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος\u0387 τί\u037e\n"
         "1\t2\t※—\tοὐλομένην, ἣ μυρί' Ἀχαιοῖς ἄλγε' ἔθηκε,\n"
         "1\t3\t— ras.\t• πολλὰς δ' ἰφθίμους ψυχὰς Ἄϊδι προΐαψεν.\n"
         "18\t605*\t⸖ ϽϾϿ\tἡρώων\n")

NOT_GREEK = "characters that are not Greek"
SIGNS = "a margin that is not the edition's signs"
FIELDS = "a book or line number"


@pytest.mark.parametrize("planted, what", [
    ('1\t9\t\t<l n="2">λόγος</l>', "markup"),
    ("1\t9\t\tλόγος</div>", "markup"),
    ('1\t9\t\t<?xml version="1.0"?>', "markup"),
    ("1\t9\t\tλόγος &amp; οὐσία", "markup"),
    ("1\t9\t\tλόγος &#955; οὐσία", "markup"),
    ("1\t9\t\t<καὶ/>", "markup"),                       # an element with a Greek name
    ("1\t9\t\t<καὶ> λόγος", "markup"),                  # Allen prints no angle brackets
    ('1\t9\t\t<seg rend="Marginalia">></seg> λόγος', "markup"),   # the export's own margin
    # beta code: the TLG's own way of writing Greek, in Latin letters
    ("1\t9\t\tmh=nin a)/eide qea/", NOT_GREEK),
    ("1\t9\t\t*)axilh=os", NOT_GREEK),
    ("1\t9\t\t(mh=nin), (a)/eide), (qea/).", NOT_GREEK),   # punctuation round each word
    ("1\t9\t\tλόγος (A) οὐσία", NOT_GREEK),            # one Latin letter is enough
    ("1\t9\t\tтекст не греческий", NOT_GREEK),          # another script
    ("1\t9\t\tSing, goddess, the wrath", NOT_GREEK),
    # Latin in another dress: none of these is a "letter" to str.isalpha
    ("1\t9\t\tλόγος ⓗⓔⓛⓛⓞ", NOT_GREEK),                # circled
    ("1\t9\t\tλόγος ｈｅｌｌｏ", NOT_GREEK),           # fullwidth
    ("1\t9\t\tλόγος\u0363", NOT_GREEK),                 # a combining Latin a
    ("1\t9\t\tλόγος 𝛼", NOT_GREEK),                     # a mathematical alpha is not a Greek letter
    ("1\t9\t\tλόγος ᵞ", NOT_GREEK),                # MODIFIER LETTER SMALL GREEK GAMMA: Greek in name only
    ("1\t9\t\tλόγος 12", NOT_GREEK),                    # digits belong in the number field
    ("1\t9\t\tλόγος — ἔργον", NOT_GREEK),               # the obelos belongs in the margin
    ("1\t9\t\tλόγος\rοὐσία", "a control character"),
    ("1\t9\t\tλόγος\x00οὐσία", "a control character"),
    ("1\t9\t\tλόγος\u00a0οὐσία", "a control character"),
    # the margin: the signs and the two words, nothing else
    ("1\t9\tmh=nin\tλόγος", SIGNS),
    ("1\t9\tcorr\tλόγος", SIGNS),
    ("1\t9\t> corr. a)/eide\tλόγος", SIGNS),
    ("1\t9\tλόγος\tλόγος", SIGNS),                      # Greek hidden in the margin
    ("1\t9\t>corr.\tλόγος", SIGNS),                     # a word run into a sign
    ("1\t9\t•\tλόγος", SIGNS),                          # the bullet stands in the text, where the edition prints it
    ("1\t9\t<seg>\tλόγος", SIGNS),
    # text hidden in the other fields, or in spare ones
    ("1\t9\t\tm\th\tα", FIELDS),
    ("mhnin\t9\t\tλόγος", FIELDS),
    ("1\tqea\t\tλόγος", FIELDS),
    ("1\ta)/eide\t\tλόγος", FIELDS),
    ("01\t9\t\tλόγος", FIELDS),                         # reads back as book 1: two spellings, one book
    ("0\t9\t\tλόγος", FIELDS),
    ("1\t09\t\tλόγος", FIELDS),
    ("1\t9a\t\tλόγος", FIELDS),
    ("1\t605**\t\tλόγος", FIELDS),
    ("1\t\t\tλόγος", FIELDS),
    ("# mh=nin a)/eide qea/", FIELDS),                  # a "heading" below the heading
    ("λόγος", FIELDS),
])
def test_forbidden_catches_each_planted_case(planted, what):
    problems = gl.forbidden(CLEAN + planted + "\n")
    assert any(what in p for p in problems), problems


def test_forbidden_catches_one_bad_line_at_the_end_of_a_long_clean_file():
    # No share of the file is allowed to be something else: one line fails it.
    long = CLEAN + "".join(f"2\t{n}\t>\tλόγος τῆς οὐσίας ἕτερος\n" for n in range(1, 5000))
    assert gl.forbidden(long) == []
    assert any(NOT_GREEK in p for p in gl.forbidden(long + "2\t5000\t\t(mh=nin).\n"))


@pytest.mark.parametrize("text", [
    # anything above the three heading lines, in place of them, or between them
    '# <l n="1">mh=nin a)/eide qea/</l>\n' + CLEAN,
    CLEAN.replace("# edition: e\n", "# edition: e\n# mh=nin a)/eide qea/\n"),
    CLEAN.replace("# work: T\n", "# work: mh=nin a)/eide\n"),
    CLEAN.replace("# edition: e\n", "# note: mh=nin a)/eide qea/\n"),
    "# work: T\n# columns: book\tn\tsigla\ttext\n",
    "",
])
def test_forbidden_refuses_a_file_that_does_not_open_with_the_three_heading_lines(text):
    assert any("not a line file" in p for p in gl.forbidden(text))


def test_forbidden_checks_the_heading_lines_too():
    assert any("markup" in p for p in gl.forbidden(CLEAN.replace("# edition: e", "# edition: <TEI>e</TEI>")))
    for columns in ("mh=nin a)/eide", "mhnin\tn\tsigla\ttext", "book\tn\ttext", "Stephanus-page\tsection\tn\ttext"):
        assert any("not a line file" in p for p in gl.forbidden(CLEAN.replace("book\tn\tsigla\ttext", columns)))


def test_forbidden_passes_the_clean_file():
    assert gl.forbidden(CLEAN) == []


def test_forbidden_fails_a_file_whose_lines_hold_no_letters():
    assert any("no letters" in p for p in gl.forbidden(H + "1\tt\t\t\n1\t1\t—\t' .\n"))


def test_there_is_no_named_exception():
    # Aristotle's guard has one (an editor's cross-reference). Homer's needs
    # none; one added here must come with a test of its own.
    assert gl.NOT_GREEK_OK == {}


# ---- a line file gives stage 1 what the XML gives it -----------------------

def _manifest() -> Manifest:
    data = {"work": {"id": "t", "tlg_author": "0012", "tlg_work": "001", "greek_edition": "e",
                     "greek_source_kind": "tlg"},
            "citation": {"scheme": "verse-line"},
            "books": [{"n": 1, "start": "1.1", "end": "1.9"}, {"n": 2, "start": "2.1", "end": "2.9"}]}
    return Manifest(data, Path("T.yaml"))


# Book 2 before book 1 (the spine sorts them); a title line in its <label>; a
# margin sign, a combined one, and a sign with a word; the bullet; a starred
# number; a line printed twice (the first wins); a <pb/>, a <space/>, a
# comment, and a <hi> inside lines; and an ano teleia that NFC changes.
CASE = (
    _book("2", '<l n="1">ἄνδρα μοι ἔννεπε</l>')
    + _book("1", '<l n="t"><label type="head">ΙΛΙΑΔΟΣ Α</label> </l>'
                 '<l n="1">Μῆνιν   ἄειδε<pb/> θεὰ</l>'
                 '<l n="2"><seg rend="Marginalia">&gt; corr.</seg> οὐλομένην\u0387</l>'
                 '<l n="3"><seg rend="Marginalia">※—</seg> πολλὰς<!-- x --> δ\' <hi rend="x">ἰφθίμους</hi></l>'
                 '<l n="4">• ἡρώων, αὐτοὺς <space/></l>'
                 '<l n="5*">οἰωνοῖσί τε πᾶσι</l>'
                 '<l n="4">δεύτερον</l>')
    + '<l n="9">ἔξω</l>')

ROWS = [
    gl.Row("2", "1", "", "ἄνδρα μοι ἔννεπε"),
    gl.Row("1", "t", "", ""),
    gl.Row("1", "1", "", "Μῆνιν ἄειδε θεὰ"),
    gl.Row("1", "2", "> corr.", "οὐλομένην\u0387"),
    gl.Row("1", "3", "※—", "πολλὰς δ' ἰφθίμους"),
    gl.Row("1", "4", "", "• ἡρώων, αὐτοὺς"),
    gl.Row("1", "5*", "", "οἰωνοῖσί τε πᾶσι"),
    gl.Row("1", "4", "", "δεύτερον"),
]
SPINE = [
    ("1:1", [{"n": 1, "text": "Μῆνιν ἄειδε θεὰ"},
             {"n": 2, "text": "οὐλομένην\u00b7", "sigla": "> corr."},
             {"n": 3, "text": "πολλὰς δ' ἰφθίμους", "sigla": "※—", "bracketed": True},
             {"n": 4, "text": "ἡρώων, αὐτοὺς", "sigla": "•"},
             {"n": 5, "text": "οἰωνοῖσί τε πᾶσι"}]),
    ("2:2", [{"n": 1, "text": "ἄνδρα μοι ἔννεπε"}]),
]


def test_the_line_file_reads_back_and_makes_the_same_spine(tmp_path):
    manifest = _manifest()
    xml = _xml(tmp_path, CASE)
    rows = gl.rows_from_xml(xml)
    assert len(rows) == CASE.count("<l ") - 1           # every line in a book, none dropped
    assert rows == ROWS                                  # written out by hand, above
    text = gl.format_tsv(rows, "T", "e")
    assert gl.parse_tsv(text) == rows
    assert gl.forbidden(text) == []
    tsv = tmp_path / "T.tsv"
    tsv.write_text(text, encoding="utf-8")
    spine = s1.parse_rows(gl.load(tsv), manifest, supplement={})
    assert spine == s1.parse_spine(xml, manifest, supplement={})
    # ... and both are the spine a reader of the case would write by hand
    assert [(s["id"], s["lines"]) for s in spine["segments"]] == SPINE
    assert spine["headings"] == [{"column": "1", "n": "t", "text": ""}]
    assert spine["normalized_line_attrs"] == [{"book": 1, "raw": "5*", "normalized": 5}]
    assert spine["skipped_line_attrs"] == {"t": 1} and spine["title_lines_skipped"] == 1


def test_a_sign_moved_in_the_line_file_moves_in_the_spine(tmp_path):
    # The comparison above would pass a reader that ignored the margin on both
    # sides; this one would not.
    rows = list(ROWS)
    rows[2] = gl.Row("1", "1", "—", "Μῆνιν ἄειδε θεὰ")
    rows[4] = gl.Row("1", "3", "", "πολλὰς δ' ἰφθίμους")
    tsv = tmp_path / "T.tsv"
    tsv.write_text(gl.format_tsv(rows, "T", "e"), encoding="utf-8")
    lines = {l["n"]: l for l in s1.parse_rows(gl.load(tsv), _manifest(), supplement={})["segments"][0]["lines"]}
    assert lines[1] == {"n": 1, "text": "Μῆνιν ἄειδε θεὰ", "sigla": "—", "bracketed": True}
    assert lines[3] == {"n": 3, "text": "πολλὰς δ' ἰφθίμους"}


def test_the_supplement_applies_to_a_line_file_as_to_the_xml(tmp_path):
    rows = [gl.Row("8", "547", "", "α"), gl.Row("8", "549", "", "β")]
    spine = s1.parse_rows(rows, _manifest())
    assert [l["n"] for l in spine["segments"][0]["lines"]] == [547, 548, 549, 550, 551, 552]


def test_stage_1_reads_the_committed_file_and_names_extract_when_it_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(gl, "CORPUS_DIR", tmp_path)
    with pytest.raises(FileNotFoundError, match="homer_pipeline.extract --work T"):
        s1.read_lines(_manifest())
    (tmp_path / "T.tsv").write_text(gl.format_tsv(ROWS, "T", "e"), encoding="utf-8")
    assert s1.read_lines(_manifest()) == ROWS
