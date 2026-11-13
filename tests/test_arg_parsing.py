import argparse

import pytest

from pre_commit_check_office_metadata.check_metadata import _extension_set, _tag_set, main
from tests import TEST_DATA_DIR

SAMPLE_FILE = str(TEST_DATA_DIR / "sample_file.xlsx")


def test_extension_set_parsing() -> None:
    assert _extension_set(" .DOCX , .xlsx,") == {".docx", ".xlsx"}
    assert _extension_set("") == set()


@pytest.mark.parametrize("value", ("docx", ".docx,xlsx", "a.xlsx", "src/a.xlsx"))
def test_extension_set_invalid_raises(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="invalid extension"):
        _extension_set(value)


def test_tag_set_parsing() -> None:
    assert _tag_set(" Application , Company,") == {"Application", "Company"}
    assert _tag_set("") == set()


@pytest.mark.parametrize("value", ("a.xlsx", "src/a", "creator,1abc"))
def test_tag_set_invalid_raises(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="invalid tag"):
        _tag_set(value)


def test_main_options_before_filenames() -> None:
    # pre-commit places user-provided args before the filenames
    assert main(["--extensions", ".docx,.xlsx", SAMPLE_FILE]) == 1
    assert main(["--extensions=.docx", SAMPLE_FILE]) == 0


def test_main_comma_separated_tags(capsys: pytest.CaptureFixture) -> None:
    assert main(["--app-exclude=Company", "--core-exclude=", SAMPLE_FILE]) == 1
    out = capsys.readouterr().out
    assert "docProps/app.xml: Company" in out
    assert "Application" not in out


def test_main_empty_tags_disable_checks() -> None:
    assert main(["--app-exclude=", "--core-exclude=", SAMPLE_FILE]) == 0


def test_main_space_separated_values_error(capsys: pytest.CaptureFixture) -> None:
    with pytest.raises(SystemExit) as e:
        main(["--app-exclude", "Application", "Company", SAMPLE_FILE])

    assert e.value.code == 2
    err = capsys.readouterr().err
    assert "file(s) not found: Company" in err
    assert "comma-separated" in err


def test_main_invalid_extension_error(capsys: pytest.CaptureFixture) -> None:
    with pytest.raises(SystemExit) as e:
        main(["--extensions=xlsx", SAMPLE_FILE])

    assert e.value.code == 2
    assert "invalid extension(s): xlsx" in capsys.readouterr().err
