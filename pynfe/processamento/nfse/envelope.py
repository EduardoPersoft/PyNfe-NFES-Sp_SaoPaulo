from lxml import etree
from pynfe.utils.flags import (NAMESPACE_SOAP,
NAMESPACE_XSI,
NAMESPACE_XSD)

class Envelope(object):

    def envelopar(self, dados):
        soap2 = "http://schemas.xmlsoap.org/soap/envelope/"
        raiz = etree.Element(
            "{%s}Envelope" % soap2,
            nsmap={"xsi": NAMESPACE_XSI, "xsd": NAMESPACE_XSD, "soap": soap2}
        )
        b = etree.SubElement(raiz, "{%s}Body" % soap2)
        b.append(dados)
        return raiz
