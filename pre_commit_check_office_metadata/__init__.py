import xml.etree.ElementTree as ET

FLAG_TAGS = {
    "docProps/app.xml": ["Application", "Company"],
    "docProps/core.xml": ["Creator", "lastModifiedBy"],
}

OFFICE_EXTENSIONS = {".xlsx", ".docx", ".pptx"}


def _element_name_from_tag(elem: ET.Element) -> str:
    _, name = elem.tag.split("}")
    return name
