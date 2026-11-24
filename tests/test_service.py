import pytest

from actiontrack import service
from conftest import TODAY, write_note

PN = ["Priya Nair", "Rahul Mehta"]


def test_only_md_files(tmp_path, store):  # T-01
    write_note(tmp_path, "a.md", "2026-09-01", PN, ["- [ ] Priya N. to do a by Friday"])
    (tmp_path / "b.txt").write_text("- [ ] Priya to do b")
    (tmp_path / "sub").mkdir()
    write_note(tmp_path / "sub", "c.md", "2026-09-01", PN, ["- [ ] Priya N. to do c"])
    r = service.ingest(store, str(tmp_path))
    assert r.read == 1 and r.skipped == [] and len(store.all_items()) == 1


def test_bad_folder(store):  # T-02 (service level)
    with pytest.raises(service.InvalidFolder):
        service.ingest(store, "does-not-exist")


def test_idempotent_and_done_survives(tmp_path, store):  # T-04
    write_note(tmp_path, "a.md", "2026-09-01", PN, ["- [ ] Priya N. to do a by Friday", "- [ ] Rahul to do b"])
    r1 = service.ingest(store, str(tmp_path))
    assert r1.added == 2
    service.mark_done(store, 1, TODAY)
    r2 = service.ingest(store, str(tmp_path))
    assert (r2.added, r2.updated) == (0, 0)
    assert store.get(1).status == "done"


def test_dedup_acme_and_never_reopen(tmp_path, store):  # T-17, T-18
    at = ["Priya Nair", "Rahul Mehta", "Anita Desai", "Sam Okafor"]
    write_note(tmp_path, "1.md", "2026-09-01", at, ["- [ ] Priya to send the revised quote to Acme by Friday"])
    write_note(tmp_path, "2.md", "2026-09-08", at, ["- [ ] Priya N. to send revised quote to Acme — by Friday"])
    write_note(tmp_path, "3.md", "2026-09-15", at, ["- [x] Priya to send the revised quote to Acme"])
    write_note(tmp_path, "4.md", "2026-09-22", at, ["- [ ] Priya to send the revised quote to Acme"])
    service.ingest(store, str(tmp_path))
    items = store.all_items()
    assert len(items) == 1
    it = items[0]
    assert it.owner == "Priya Nair" and it.status == "done"
    assert it.sources == ["1.md", "2.md", "3.md", "4.md"]
    assert str(it.due) == "2026-09-11" and not it.due_defaulted   # S-5: 3.md/4.md state no due, keep it


def test_distinct_tasks_not_merged(tmp_path, store):  # T-19
    write_note(tmp_path, "1.md", "2026-09-01", PN, ["- [ ] Rahul to share first wireframes", "- [ ] Rahul to share updated wireframes"])
    service.ingest(store, str(tmp_path))
    assert len(store.all_items()) == 2


def test_default_due_and_ambiguity_report(tmp_path, store):  # T-16, T-12
    at = ["Priya Nair", "Priya Shah"]
    write_note(tmp_path, "1.md", "2026-09-23", at, ["- [ ] Priya to sign off the checklist", "- [ ] Everyone to submit goals"])
    r = service.ingest(store, str(tmp_path))
    items = store.all_items()
    assert any(i.owner_status == "ambiguous" and i.owner == "Priya" for i in items)
    assert len([i for i in items if i.task == "submit goals"]) == 2           # Everyone -> one per attendee
    assert all(i.due is None and i.due_defaulted for i in items)
    assert service.effective(items[0]).isoformat() == "2026-09-30"
    assert len(r.ambiguous) == 1 and len(r.no_due) == 3


def test_order_independent(tmp_path):  # T-34
    from actiontrack.store import Store
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir(), b.mkdir()
    at = ["Sam Okafor", "Rahul Mehta"]
    write_note(a, "1.md", "2026-09-01", at, ["- [ ] Sam to ship it by Friday"])
    write_note(a, "2.md", "2026-09-01", ["Sam Okafor", "Rahul Verma"], ["- [x] Sam to ship it"])
    write_note(b, "1.md", "2026-09-01", ["Sam Okafor", "Rahul Verma"], ["- [x] Sam to ship it"])
    write_note(b, "2.md", "2026-09-01", at, ["- [ ] Sam to ship it by Friday"])
    snaps = []
    for folder in (a, b):
        s = Store(str(folder / "x.db"))
        service.ingest(s, str(folder))
        snaps.append(sorted((i.owner, i.task, i.status, str(i.due)) for i in s.all_items()))
        s.close()
    assert snaps[0] == snaps[1]


def test_overdue_rules(tmp_path, store):  # T-20
    write_note(tmp_path, "1.md", "2026-09-01", PN, [
        "- [ ] Rahul to a by 2026-09-30", "- [x] Rahul to b by 2026-09-30", "- [ ] Rahul to c by 2026-10-05", "- [ ] Rahul to d"])
    service.ingest(store, str(tmp_path))
    od = service.list_items(store, TODAY, status="overdue")
    # d has no stated due: effective due 2026-09-08 < today, so it is overdue too; b is done, c is not due yet
    assert [i.task for i in od] == ["d", "a"]


def test_list_filters_and_order(tmp_path, store):  # T-21
    write_note(tmp_path, "1.md", "2026-09-01", PN, [
        "- [ ] Rahul to late by 2026-09-20", "- [ ] Rahul to early by 2026-09-10", "- [ ] Priya N. to other by 2026-09-12"])
    service.ingest(store, str(tmp_path))
    rows = service.list_items(store, TODAY, owner="Rahul Mehta", due_before=__import__("datetime").date(2026, 9, 15))
    assert [i.task for i in rows] == ["early"]
    assert [i.task for i in service.list_items(store, TODAY)] == ["early", "other", "late"]


def test_list_ambiguous_owner(tmp_path, store):  # T-22
    write_note(tmp_path, "1.md", "2026-09-01", ["Priya Nair", "Priya Shah"], ["- [ ] Priya N. to a by 2026-09-10", "- [ ] Priya S. to b by 2026-09-10", "- [ ] TBD to c"])
    service.ingest(store, str(tmp_path))
    with pytest.raises(service.AmbiguousOwner) as exc:
        service.list_items(store, TODAY, owner="Priya")
    assert exc.value.candidates == ["Priya Nair", "Priya Shah"]
    assert [i.task for i in service.list_items(store, TODAY, owner="Priya Nair")] == ["a"]
    assert [i.task for i in service.list_items(store, TODAY, owner="unassigned")] == ["c"]


def test_done_cases(tmp_path, store):  # T-23
    write_note(tmp_path, "1.md", "2026-09-01", PN, ["- [ ] Rahul to a"])
    service.ingest(store, str(tmp_path))
    assert service.mark_done(store, 1, TODAY) is True
    assert service.mark_done(store, 1, TODAY) is False
    with pytest.raises(service.NotFound):
        service.mark_done(store, 9999, TODAY)
    service.ingest(store, str(tmp_path))
    assert store.get(1).id == 1


def test_report_lines_unique(tmp_path, store):  # T-39
    at = ["Priya Nair", "Priya Shah", "Sam Okafor"]
    write_note(tmp_path, "1.md", "2026-09-18", at, ["- [ ] Everyone to review the prototype"])
    lines = service.ingest(store, str(tmp_path)).lines()
    assert len([l for l in lines if l.startswith("no/defaulted due")]) == 1
