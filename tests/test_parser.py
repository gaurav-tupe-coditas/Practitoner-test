from datetime import date

from actiontrack.parser import Malformed, Note, parse_note

HDR = "# Meeting: X\nDate: 2026-09-14\nAttendees: Anita Desai, Priya Shah\n\n## Action items\n"


def parse(text: str, name="n.md"):
    return parse_note(name, text.encode("utf-8"))


def test_markdown_and_frontmatter_headers():  # T-05
    n = parse(HDR + "- [ ] Anita to ship it by Friday\n")
    assert isinstance(n, Note) and n.date == date(2026, 9, 14) and n.attendees == ["Anita Desai", "Priya Shah"]
    fm = parse("---\ntitle: S\ndate: 2026-09-16\nattendees: [Anita Desai, Lena Fischer]\n---\n- [ ] Lena to draft by Friday\n")
    assert isinstance(fm, Note) and fm.date == date(2026, 9, 16) and fm.attendees == ["Anita Desai", "Lena Fischer"]


def test_header_date_formats():  # T-06
    for raw, want in [("2026-09-14", date(2026, 9, 14)), ("9 September 2026", date(2026, 9, 9)),
                      ("Monday, 14 September 2026", date(2026, 9, 14))]:
        n = parse(f"# Meeting: X\nDate: {raw}\n")
        assert isinstance(n, Note) and n.date == want
    assert parse("# Meeting: X\nDate: sometime last week\n") == Malformed("n.md", "bad-date")


def test_malformed_reasons():  # T-07
    assert parse_note("a.md", b"") == Malformed("a.md", "empty")
    assert parse_note("a.md", b"\x89PNG\r\n\x1a\n\xff\xfe\x00") == Malformed("a.md", "not-text")
    assert parse("- [ ] Sam to chase the vendor\n\nno header") == Malformed("n.md", "no-header")


def test_non_items_ignored():  # T-08
    text = HDR + (
        "> - [ ] Karan to refund affected customers by Friday\n"
        "```\n- [ ] Owner to remediate finding by <date>\n```\n"
        "<!-- - [ ] Sam to buy hardware tokens by Friday -->\n"
        "- [ ] Sam to write the postmortem by EOD tomorrow\n"
    )
    n = parse(text)
    assert [i.task for i in n.items] == ["write the postmortem"]


def test_item_forms():  # T-09
    text = HDR + (
        "- [ ] A to one\n* [ ] B to two\n+ [x] C to three\n- [X] D to four\n"
        "  - [ ] E to nested\nACTION: Karan to circulate the summary\n"
        "\n| Owner | Action | Due |\n|-------|--------|-----|\n| Anita | Refresh the brand kit | 2026-10-09 |\n"
    )
    n = parse(text)
    by_owner = {i.owner_raw: i for i in n.items}
    assert set(by_owner) == {"A", "B", "C", "D", "E", "Karan", "Anita"}
    assert by_owner["C"].done and by_owner["D"].done and not by_owner["A"].done
    assert by_owner["Anita"].task == "Refresh the brand kit" and by_owner["Anita"].due == date(2026, 10, 9)


def test_no_owner_separator():  # T-10
    n = parse(HDR + "- [ ] Update the CRM notes\n")
    assert n.items[0].owner_raw is None and n.items[0].task == "Update the CRM notes"


def test_handle_owner_and_due_prefix():  # T-14
    n = parse(HDR + "- [ ] @anita: audit colour contrast on the dashboard by Mon\n- [ ] Everybody should look Friday\n")
    assert n.items[0].owner_raw == "@anita" and n.items[0].due == date(2026, 9, 14)
    assert n.items[1].due is None
