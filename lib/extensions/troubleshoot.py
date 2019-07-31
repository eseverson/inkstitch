import logging
import textwrap

import inkex

from ..commands import add_layer_commands
from ..i18n import _
from ..svg import get_correction_transform
from ..svg.tags import (INKSCAPE_GROUPMODE, INKSCAPE_LABEL,
                        SODIPODI_ROLE, SVG_GROUP_TAG, SVG_PATH_TAG,
                        SVG_TEXT_TAG, SVG_TSPAN_TAG)
from .base import InkstitchExtension


class Troubleshoot(InkstitchExtension):

    def effect(self):
        if not self.get_elements():
            return

        logger = logging.getLogger('shapely.geos')
        level = logger.level
        logger.setLevel(logging.CRITICAL)

        self.create_troubleshoot_layer()

        error_types = set()
        for element in self.elements:
            for error in element.validation_errors():
                error_types.add(type(error))
                self.insert_invalid_pointer(error)

        logger.setLevel(level)

        if error_types:
            self.add_descriptions(error_types)
        else:
            inkex.errormsg(_("All selected shapes are valid!"))

    def insert_invalid_pointer(self, error):
        correction_transform = get_correction_transform(self.troubleshoot_layer)

        path = inkex.etree.Element(
            SVG_PATH_TAG,
            {
                "id": self.uniqueId("inkstitch__invalid_pointer__"),
                "d": "m %s,%s 4,20 h -8 l 4,-20" % (error.position.x, error.position.y),
                "style": "fill:#ff0000;stroke:#ffffff;stroke-width:0.2;",
                INKSCAPE_LABEL: _('Invalid Pointer'),
                "transform": correction_transform
            }
        )
        self.troubleshoot_layer.insert(0, path)

        text = inkex.etree.Element(
            SVG_TEXT_TAG,
            {
                "x": str(error.position.x),
                "y": str(float(error.position.y) + 30),
                "transform": correction_transform,
                "style": "fill:#ff0000;troke:#ffffff;stroke-width:0.2;font-size:8px;text-align:center;text-anchor:middle"
            }
        )
        self.troubleshoot_layer.append(text)

        tspan = inkex.etree.Element(SVG_TSPAN_TAG)
        tspan.text = error.name
        text.append(tspan)

    def create_troubleshoot_layer(self):
        svg = self.document.getroot()
        layer = svg.find(".//*[@id='__validity_layer__']")

        if layer is None:
            layer = inkex.etree.Element(
                SVG_GROUP_TAG,
                {
                    'id': '__validity_layer__',
                    INKSCAPE_LABEL: _('Troubleshoot'),
                    INKSCAPE_GROUPMODE: 'layer',
                })
            svg.append(layer)

            add_layer_commands(layer, ["ignore_layer"])
        else:
            # Clear out everything from the last run
            del layer[:]

        self.troubleshoot_layer = layer

    def add_descriptions(self, error_types):
        svg = self.document.getroot()
        text_x = str(self.unittouu(svg.get('width')) + 5)

        text_container = inkex.etree.Element(
            SVG_TEXT_TAG,
            {
                "x": text_x,
                "y": str(5),
                "style": "fill:#000000;font-size:5px;line-height:1;"
            }
        )
        self.troubleshoot_layer.append(text_container)

        text = [
            [_("Troubleshoot"), "font-weight: bold; font-size: 6px;"],
            ["", ""]
        ]

        for error in error_types:
            text.append([error.name, "font-weight: bold;"])
            description_parts = textwrap.wrap(error.description, 60)
            for description in description_parts:
                text.append([description, "font-size: 3px;"])
            text.append(["", ""])
            for step in error.steps_to_solve:
                text.append([step, "font-size: 4px;"])
            text.append(["", ""])

        explain_layer = _('It is possible, that one object contains more than one error, ' +
                          'yet there will be only one pointer per object.  Run this function again, ' +
                          'when further errors occur.  Remove pointers by deleting the layer named '
                          '"Troubleshoot" through the objects panel (Object -> Objects...).')
        explain_layer_parts = textwrap.wrap(explain_layer, 60)
        for description in explain_layer_parts:
            text.append([description, "font-style: italic; font-size: 3px;"])

        for text_line in text:
            tspan = inkex.etree.Element(
                SVG_TSPAN_TAG,
                {
                    SODIPODI_ROLE: "line",
                    "style": text_line[1]
                }
            )
            tspan.text = text_line[0]
            text_container.append(tspan)