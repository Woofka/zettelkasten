from markdown.inlinepatterns import InlineProcessor
from markdown.extensions import Extension
import xml.etree.ElementTree as etree


class StrikeInlineProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        el = etree.Element('del')
        el.text = m.group(1)
        return el, m.start(0), m.end(0)


class StrikeExtension(Extension):
    def extendMarkdown(self, md):
        STRIKE_PATTERN = r'~~(.*?)~~'
        md.inlinePatterns.register(StrikeInlineProcessor(STRIKE_PATTERN, md), 'strike', 175)
