import xml.etree.ElementTree as ET
import zipfile
from functools import partial
from pathlib import Path

import pytest

from pre_commit_check_office_metadata.check_metadata import (
    MetadataFoundError,
    _check_attributes,
    check_document,
    main,
)
from tests import TEST_DATA_DIR

APP_XML = (
    '<?xml version="1.0" encoding="{encoding}" standalone="yes"?>'
    '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
    "</Properties>"
)
CORE_XML = (
    '<?xml version="1.0" encoding="{encoding}" standalone="yes"?>'
    "<cp:coreProperties"
    ' xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"'
    ' xmlns:dc="http://purl.org/dc/elements/1.1/">'
    "<dc:creator>Álvaro</dc:creator>"
    "</cp:coreProperties>"
)


def _make_doc(dst: Path, app_xml: bytes, core_xml: bytes) -> Path:
    """Build a minimal Office-like zip containing only the provided metadata XML files."""
    with zipfile.ZipFile(dst, "w") as zf:
        zf.writestr("docProps/app.xml", app_xml)
        zf.writestr("docProps/core.xml", core_xml)

    return dst


def test_error_report(capsys: pytest.CaptureFixture) -> None:
    err = MetadataFoundError("Hello, world!", {"path_to/some.xml": {"Child"}})
    err.report()

    captured = capsys.readouterr()
    assert captured.out == "    path_to/some.xml: Child\n"


def test_check_attributes() -> None:
    zf = zipfile.Path(TEST_DATA_DIR / "sample_file.xlsx")
    doc_path = zf / "docProps/app.xml"
    root = ET.fromstring(doc_path.read_text())

    truth_match = {"Application", "Company"}
    assert _check_attributes(root, flag_tags={"Application", "Company"}) == truth_match


def test_check_attributes_core() -> None:
    zf = zipfile.Path(TEST_DATA_DIR / "sample_file.xlsx")
    doc_path = zf / "docProps/core.xml"
    root = ET.fromstring(doc_path.read_text())

    truth_match = {"creator", "lastModifiedBy"}
    assert _check_attributes(root, flag_tags={"creator", "lastModifiedBy"}) == truth_match


TEST_FILTERS = {
    "docProps/app.xml": {"Application", "Company"},
    "docProps/core.xml": {"creator", "lastModifiedBy"},
}
CHECK_DOC_P = partial(check_document, filters=TEST_FILTERS)


def test_check_document_missing_xml_raises() -> None:
    with pytest.raises(ValueError, match="not found"):
        CHECK_DOC_P(TEST_DATA_DIR / "sample_file_missing_app_xml.xlsx")


def test_check_document_no_match_passthrough() -> None:
    CHECK_DOC_P(TEST_DATA_DIR / "sample_file_stripped.xlsx")


def test_check_document_match_raises() -> None:
    with pytest.raises(MetadataFoundError):
        CHECK_DOC_P(TEST_DATA_DIR / "sample_file.xlsx")


def test_check_document_not_zip_raises(tmp_path: Path) -> None:
    # Password-protected Office files are OLE compound files rather than zip archives
    doc = tmp_path / "encrypted.docx"
    doc.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 504)

    with pytest.raises(ValueError, match="Not a valid zip archive"):
        CHECK_DOC_P(doc)


def test_check_document_malformed_xml_raises(tmp_path: Path) -> None:
    doc = _make_doc(
        tmp_path / "malformed.xlsx",
        app_xml=b"<Properties",
        core_xml=CORE_XML.format(encoding="UTF-8").encode("utf-8"),
    )

    with pytest.raises(ValueError, match="docProps/app.xml could not be parsed"):
        CHECK_DOC_P(doc)


@pytest.mark.parametrize("encoding", ("UTF-8", "UTF-16"))
def test_check_document_non_ascii_metadata(tmp_path: Path, encoding: str) -> None:
    # Decoding must follow the XML declaration rather than the system's locale encoding
    doc = _make_doc(
        tmp_path / "non_ascii.xlsx",
        app_xml=APP_XML.format(encoding=encoding).encode(encoding),
        core_xml=CORE_XML.format(encoding=encoding).encode(encoding),
    )

    with pytest.raises(MetadataFoundError) as e:
        CHECK_DOC_P(doc)

    assert e.value.details["docProps/core.xml"] == {"creator"}


def test_main_invalid_document_reported(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    doc = tmp_path / "not_a_zip.xlsx"
    doc.write_text("Hello, world!")

    assert main([str(doc)]) == 1
    assert "Not a valid zip archive" in capsys.readouterr().out
