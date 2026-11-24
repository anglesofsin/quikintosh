"""Keep Nautilus native, while allowing file content behind its toolbar."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def patch_window(source, destination):
    tree = ET.parse(source)
    matches = tree.findall(".//object[@class='AdwOverlaySplitView']/property[@name='content']/object[@class='AdwToolbarView']")
    if len(matches) != 1:
        raise ValueError('The Nautilus content toolbar template has changed; refusing an ambiguous overlay.')
    toolbar = matches[0]
    for name, value in [('extend-content-to-top-edge', 'true'), ('top-bar-style', 'flat')]:
        node = toolbar.find(f"property[@name='{name}']")
        if node is None:
            node = ET.SubElement(toolbar, 'property', name=name)
        node.text = value
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    tree.write(destination, encoding='utf-8', xml_declaration=True)


def patch_history(source, destination):
    tree = ET.parse(source)
    root = tree.find(".//template[@class='NautilusHistoryControls']")
    if root is None:
        raise ValueError('The Nautilus navigation template has changed.')
    style = root.find('style')
    if style is None:
        style = ET.SubElement(root, 'style')
    ET.SubElement(style, 'class', name='lickintosh-glass-navigation')
    tree.write(destination, encoding='utf-8', xml_declaration=True)


if __name__ == '__main__':
    patch_window(sys.argv[1], sys.argv[2])
    if len(sys.argv) > 3:
        patch_history(sys.argv[3], sys.argv[4])
