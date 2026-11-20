import base64
import gzip
import unittest
from lxml import etree
from pynfe.processamento.nfse import compactador


class Compactador(unittest.TestCase):

    def setUp(self) -> None:
        self.compactador = compactador.Compactador()
        self.xml = '<DPS xmlns="http://www.sped.fazenda.gov.br/nfse"><infDPS Id="DPS1"><xDesc>Serviço de manutenção</xDesc></infDPS></DPS>'

    def test_compactar_str(self):
        r = self.compactador.compactar(self.xml)
        self.assertIsInstance(r, str)
        self.assertEqual(gzip.decompress(base64.b64decode(r)).decode("utf-8"),
                         self.xml)

    def test_compactar_bytes(self):
        r = self.compactador.compactar(self.xml.encode("utf-8"))
        self.assertEqual(self.compactador.descompactar(r), self.xml)

    def test_compactar_element(self):
        r = self.compactador.compactar(etree.fromstring(self.xml))
        x = self.compactador.descompactar(r)
        self.assertTrue(x.startswith("<?xml"))
        self.assertIn("Serviço de manutenção", x)

    def test_descompactarXml(self):
        r = self.compactador.compactar(self.xml)
        x = self.compactador.descompactarXml(r)
        self.assertEqual(x.tag, "{http://www.sped.fazenda.gov.br/nfse}DPS")
        self.assertEqual(x[0].get("Id"), "DPS1")


if __name__ == '__main__':
    unittest.main()
