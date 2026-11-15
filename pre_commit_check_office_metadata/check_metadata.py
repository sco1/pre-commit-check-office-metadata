import argparse
import re
import sys
import typing as t
import xml.etree.ElementTree as ET
import zipfile
from collections import abc
from pathlib import Path

from pre_commit_check_office_metadata import FLAG_TAGS, OFFICE_EXTENSIONS, _element_name_from_tag

EXTENSION_PATTERN = re.compile(r"^\.[A-Za-z0-9]+$")
TAG_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


def _split_csv(value: str) -> set[str]:
    return {v.strip() for v in value.split(",") if v.strip()}


def _extension_set(value: str) -> set[str]:
    """Parse a comma-separated list of file extensions, e.g. `".docx,.xlsx"`."""
    extensions = {ex.lower() for ex in _split_csv(value)}
    invalid = sorted(ex for ex in extensions if not EXTENSION_PATTERN.match(ex))
    if invalid:
        raise argparse.ArgumentTypeError(
            f"invalid extension(s): {', '.join(invalid)} (expected e.g. '.docx,.xlsx')"
        )

    return extensions


def _tag_set(value: str) -> set[str]:
    """Parse a comma-separated list of XML tag names, e.g. `"creator,lastModifiedBy"`."""
    tags = _split_csv(value)
    invalid = sorted(tag for tag in tags if not TAG_PATTERN.match(tag))
    if invalid:
        raise argparse.ArgumentTypeError(
            f"invalid tag name(s): {', '.join(invalid)} (expected e.g. 'Application,Company')"
        )

    return tags


class MetadataFoundError(Exception):  # noqa: D101
    def __init__(self, msg: str, details: dict[str, set[str]]) -> None:
        super().__init__(msg)
        self.details = details

    def report(self) -> None:
        """Print the found tags for each XML file, sorted for deterministic output."""
        for xml_path, found_tags in sorted(self.details.items()):
            if not found_tags:
                continue

            print(f"    {xml_path}: {', '.join(sorted(found_tags, key=str.casefold))}")


def _check_attributes(root: ET.Element, flag_tags: set[str]) -> set[str]:
    tags_with_text = {_element_name_from_tag(c) for c in root if c.text}
    return tags_with_text & flag_tags


def check_document(doc: Path, filters: dict[str, set[str]]) -> None:
    """
    Check the provided Office document for the presence of data in any of the specified tags.

    `filters` is provided as a dictionary whose keys are the path of an XML file, relative to the
    document root, and values are the tags to examine for any attached data.

    All matching items are bundled into a single exception per Office document.

    A `ValueError` is raised if the document cannot be read as an Office document, e.g. it is not a
    valid zip archive (such as a password-protected file), a metadata XML file is missing, or a
    metadata XML file cannot be parsed.
    """
    try:
        zf = zipfile.Path(doc)
    except zipfile.BadZipFile as e:
        raise ValueError(
            "Not a valid zip archive; the file may be corrupt or password-protected"
        ) from e

    found = {}
    for xml_path, flag_tags in filters.items():
        doc_path = zf / xml_path
        if not doc_path.exists():
            raise ValueError(f"{xml_path} not found in document metadata")

        # Parse from bytes so the XML declaration determines the encoding, rather than the system's
        # locale encoding (e.g. cp1252 on Windows)
        try:
            root = ET.fromstring(doc_path.read_bytes())
        except ET.ParseError as e:
            raise ValueError(f"{xml_path} could not be parsed: {e}") from e

        hits = _check_attributes(root, flag_tags)
        if hits:
            found[xml_path] = hits

    if found:
        raise MetadataFoundError("Metadata found", found)


def main(argv: t.Optional[abc.Sequence[str]] = None) -> int:  # noqa: D103
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*", type=Path)
    parser.add_argument("--extensions", type=_extension_set, default=set(OFFICE_EXTENSIONS))
    parser.add_argument("--app-exclude", type=_tag_set, default=set(FLAG_TAGS["docProps/app.xml"]))
    parser.add_argument(
        "--core-exclude", type=_tag_set, default=set(FLAG_TAGS["docProps/core.xml"])
    )
    args = parser.parse_args(argv)

    missing = [str(file) for file in args.filenames if not file.is_file()]
    if missing:
        parser.error(
            f"file(s) not found: {', '.join(missing)}. "
            "Option values must be comma-separated, e.g. --app-exclude=Application,Company"
        )

    filters = {
        "docProps/app.xml": args.app_exclude,
        "docProps/core.xml": args.core_exclude,
    }

    ec = 0
    for file in args.filenames:
        if file.suffix.lower() not in args.extensions:
            continue

        try:
            check_document(file, filters)
        except MetadataFoundError as e:
            print(f"{file}:")
            e.report()
            ec = 1
        except ValueError as e:
            print(f"{file}:\n    {e}")
            ec = 1

    return ec


if __name__ == "__main__":
    sys.exit(main())
