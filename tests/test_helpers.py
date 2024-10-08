import xml.etree.ElementTree as ET

from pre_commit_check_office_metadata import _element_name_from_tag


def test_element_name_from_tag() -> None:
    lmnt = ET.Element("{http://some.schema}Application")
    assert _element_name_from_tag(lmnt) == "Application"
