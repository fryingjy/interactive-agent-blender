from tools.audit_repository import missing_document_links


def test_missing_links_and_reference_definitions(tmp_path):
    doc = tmp_path / "README.md"
    doc.write_text('[missing](gone.md#heading)\n[ref]: absent.json "Title"\n', encoding="utf-8")
    assert missing_document_links(doc, tmp_path) == [
        {"document": "README.md", "destination": "absent.json"},
        {"document": "README.md", "destination": "gone.md#heading"},
    ]


def test_local_paths_fragments_and_remote_links(tmp_path):
    (tmp_path / "a file.md").touch()
    docs = tmp_path / "docs"
    docs.mkdir()
    doc = docs / "index.md"
    doc.write_text('[a](../a%20file.md#x) [b](</a file.md>) [self](#x) '
                   '[remote](https://example.com/missing) [mail](mailto:a@b.test)', encoding="utf-8")
    assert missing_document_links(doc, tmp_path) == []


def test_code_examples_are_not_links(tmp_path):
    doc = tmp_path / "README.md"
    doc.write_text('```md\n[x](not-a-file)\n```\n~~~\n[x](not-a-file)\n~~~\n'
                   '`[x](not-a-file)`\n', encoding="utf-8")
    assert missing_document_links(doc, tmp_path) == []


def test_links_cannot_escape_repository(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (tmp_path / "outside.md").touch()
    doc = root / "README.md"
    doc.write_text('[x](../outside.md)', encoding="utf-8")
    assert len(missing_document_links(doc, root)) == 1
