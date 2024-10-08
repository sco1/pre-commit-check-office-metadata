import xml.etree.ElementTree as ET
import zipfile
from functools import partial

import pytest

from pre_commit_check_office_metadata.check_metadata import (
    MetadataFoundError,
    _check_attributes,
    check_document,
)
from tests import TEST_DATA_DIR


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


TEST_FILTERS = {
    "docProps/app.xml": {"Application", "Company"},
    "docProps/core.xml": {"Creator", "lastModifiedBy"},
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
