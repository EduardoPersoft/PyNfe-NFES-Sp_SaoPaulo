import base64
import gzip
from lxml import etree


class Compactador(object):
    """Compacta e descompacta documentos XML no padrão GZip com
    representação base64, usado pela API da NFS-e Nacional
    (dpsXmlGZipB64, nfseXmlGZipB64, eventoXmlGZipB64...).

    Fica no módulo de NFS-e, e não em pynfe/utils, para manter as
    alterações isoladas até a validação pelo mantenedor do projeto.
    """

    def compactar(self, xml):
        """Recebe o XML (etree._Element, str ou bytes) e devolve uma str
        com o XML em UTF-8 compactado em GZip e codificado em base64."""
        if isinstance(xml, etree._Element):
            xml = etree.tostring(xml, encoding="UTF-8", xml_declaration=True)
        elif isinstance(xml, str):
            xml = xml.encode("utf-8")
        return base64.b64encode(gzip.compress(xml)).decode("ascii")

    def descompactar(self, dados):
        """Recebe a str em base64 devolvida pela API e retorna o XML
        como str."""
        return gzip.decompress(base64.b64decode(dados)).decode("utf-8")

    def descompactarXml(self, dados):
        """Igual a descompactar, mas devolve o XML como etree._Element."""
        return etree.fromstring(gzip.decompress(base64.b64decode(dados)))
