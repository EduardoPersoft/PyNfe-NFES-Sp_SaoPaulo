from lxml import etree
from pynfe.utils.flags import (NAMESPACE_SOAP,
NAMESPACE_XSI,
NAMESPACE_XSD)

class Envelope(object):

    def envelopar(self, dados):
        raiz = etree.Element(
            "{%s}Envelope" % NAMESPACE_SOAP,
            nsmap={"xsi": NAMESPACE_XSI, "xsd": NAMESPACE_XSD, "soap": NAMESPACE_SOAP}
        )
        b = etree.SubElement(raiz, "{%s}Body" % NAMESPACE_SOAP)
        b.append(dados)
        return raiz
