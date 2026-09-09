# Test_files

Input files for the tests on `app/pdf.py`. Each one exists to push
`extract_text()` down a different path.

The routing decision being tested is this line in `app/pdf.py`:

```python
if len(text) >= MIN_PER_PAGE * len(reader.pages):   # MIN_PER_PAGE = 100
```

pypdf reads the text layer first. If there is enough of it the file is
digital and we return that text. If there is not, the file is a scan and OCR
runs as the fallback.

## Built by a script

`uv run python -m scripts.make_test_files` regenerates these four. Do not
edit them by hand - change the script instead.

| File | Pages | Text layer | What it proves |
|---|---|---|---|
| `digital_multipage.pdf` | 3 | 1228 chars (409/page) | Well over the 300 threshold, so OCR must **never** be called |
| `scanned_multipage.pdf` | 2 | 0 chars | Under the 200 threshold, so OCR **must** be called |
| `mixed.pdf` | 3 | 831 chars, all on pages 1-2 | Page 3 is a scan. See below - this one currently fails |
| `locked.pdf` | 3 | password protected | pypdf opens it, then raises `FileNotDecryptedError` on the pages |

The multi-page counts matter. `MIN_PER_PAGE * len(reader.pages)` multiplies by
the page count, and with only 1-page files that multiplication would never be
tested - 100 x 1 and plain 100 look identical. Three pages and two pages make
the two thresholds different numbers (300 and 200), so a broken calculation
shows up.

`scanned_multipage.pdf` (~292 KB) and `mixed.pdf` (~98 KB) are the large ones.
Scans are images, and images are not small.

### What `mixed.pdf` shows

A JD where the first two pages are typed and the last is a scanned signature
page. Measured:

```
page 1 -> 408 chars     page 2 -> 423 chars     page 3 -> 0 chars
total 831 >= 300        so OCR is skipped
```

The check adds up text across the **whole** document, not per page. Two good
pages easily clear a three-page threshold, so OCR never runs and page 3's
words are dropped - no error, no warning, and the LLM is handed an incomplete
JD. The phrases `Appendix A` and `Signature on file` appear only on that page,
so a test can search for them to prove whether it survived.

This is a real shape of file to be handed, so it is worth a test rather than
a shrug. Whether to fix it (check per page instead of in total) is a separate
decision - the test should record the behaviour either way.

## Collected by hand

Real files, because a generated scan is always cleaner than a real one -
straight, evenly lit, one font. A phone photo of a printed page is the case
OCR actually has to survive.

| File | What it is |
|---|---|
| `digital_jd_1.pdf` | Normal JD exported from Word or Google Docs |
| `digital_jd_2.pdf` | Same, from a different source |
| `scanned_jd_1.pdf` | Real scan or phone photo, no text layer |
| `scanned_jd_2.pdf` | Same, ideally more than one page |
| `corrupt.pdf` | Truncated or non-PDF bytes with a `.pdf` name |

Before trusting a hand-collected scan, check it really has no text layer -
many scanner apps quietly run their own OCR and write the result into the
file, which would make it behave as a digital PDF and stop testing our OCR
path at all:

```
uv run python -c "from pypdf import PdfReader; r=PdfReader('Test_files/scanned_jd_1.pdf'); print(len(r.pages), 'pages,', sum(len(p.extract_text() or '') for p in r.pages), 'chars')"
```

Close to 0 chars means it is a genuine scan.

## Deliberately not here

These cases are built inside the test file, because a file on disk would say
less than one line of Python:

- invalid UTF-8 bytes - `b"\xff\xfe caf\xe9"`
- a missing filename - pass `None`
- an empty upload - `b""`
- an uppercase extension - pass `digital_multipage.pdf` as `"JD.PDF"`
- OCR failing, or returning less text than pypdf found - mock `ocr()`
- landing exactly on the threshold - monkeypatch `MIN_PER_PAGE`

## A note on `.txt`

`extract_text()` skips PDF handling entirely for non-PDF names. The existing
`demo_jds/jd_backend.txt` covers that path, so there is no `.txt` file here.
