import argparse
import sys
import typing as t
import xml.etree.ElementTree as ET
import zipfile
from collections import abc
from pathlib import Path

from pre_commit_check_office_metadata import FLAG_TAGS, OFFICE_EXTENSIONS, _element_name_from_tag


class MetadataFoundError(Exception):  # noqa: D101
    def __init__(self, msg: str, details: dict[str, set[str]]) -> None:
        super().__init__(msg)
        self.details = details

    def report(self) -> None:  # noqa: D102
        for xml_path, found_tags in self.details.items():
            print(f"    {xml_path}: {', '.join(found_tags)}")


def _check_attributes(root: ET.Element, flag_tags: set[str]) -> set[str]:
    tags_with_text = {_element_name_from_tag(c) for c in root if c.text}
    return tags_with_text & flag_tags


def check_document(doc: Path, filters: dict[str, set[str]]) -> None:
    """
    Check the provided Office document for the presence of data in any of the specified tags.

    `filters` is provided as a dictionary whose keys are the path of an XML file, relative to the
    document root, and values are the tags to examine for any attached data.

    All matching items are bundled into a single exception per Office document.
    """
    zf = zipfile.Path(doc)

    found = {}
    for xml_path, flag_tags in filters.items():
        doc_path = zf / xml_path
        if not doc_path.exists():
            raise ValueError(f"{xml_path} not found in document metadata")

        root = ET.fromstring(doc_path.read_text())
        found[xml_path] = _check_attributes(root, flag_tags)

    if any(x for x in found.values()):
        raise MetadataFoundError("Metadata found", found)


def main(argv: t.Optional[abc.Sequence[str]] = None) -> int:  # noqa: D103
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*", type=Path)
    parser.add_argument("--extensions", nargs="*", type=str, default=OFFICE_EXTENSIONS)
    parser.add_argument("--app-exclude", nargs="*", type=str, default=FLAG_TAGS["docProps/app.xml"])
    parser.add_argument(
        "--core-exclude", nargs="*", type=str, default=FLAG_TAGS["docProps/core.xml"]
    )
    args = parser.parse_args(argv)

    args.extensions = {ex.lower() for ex in args.extensions}

    filters = {
        "docProps/app.xml": set(args.app_exclude),
        "docProps/core.xml": set(args.core_exclude),
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
