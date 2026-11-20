import base64
import hashlib
import unittest
import xml.etree.ElementTree as ET
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from lxml import etree
from pynfe.entidades.certificado import CertificadoA1
from pynfe.processamento.nfse.nfse_nacional import assinatura
from pynfe.processamento.nfse.nfse_nacional import serializacao
from pynfe.processamento.nfse.nfse_nacional import validacao
from pynfe.processamento.nfse.nfse_nacional.flags import NAMESPACE_NFSE
from tests.processamento.nfse.nfse_nacional.serializacao import get_nfse

DS = "http://www.w3.org/2000/09/xmldsig#"
NS = {'n': NAMESPACE_NFSE, 'ds': DS}


def c14nTrecho(xml, tag, namespace):
    """C14N inclusivo de um trecho, sem usar o libxml2: canonicaliza o
    documento inteiro com xml.etree.ElementTree (Python puro), recorta o
    elemento e declara nele o namespace padrão herdado, como o C14N
    inclusivo de um trecho exige."""
    doc = ET.canonicalize(xml_data=xml.decode("utf-8"))
    inicio = doc.index("<%s" % tag)
    fim = doc.index("</%s>" % tag) + len("</%s>" % tag)
    trecho = doc[inicio:fim]
    if not trecho.startswith('<%s xmlns=' % tag):
        trecho = '<%s xmlns="%s"%s' % (tag, namespace, trecho[len(tag) + 1:])
    return trecho.encode("utf-8")


class Assinatura(unittest.TestCase):

    def setUp(self) -> None:
        self.certificado = "./tests/certificado.pfx"
        self.senha = bytes("123456", encoding="utf-8")
        self.assinatura = assinatura.Assinatura(self.certificado, self.senha)
        self.dps = serializacao.Serializacao().gerar(get_nfse())
        self.id = self.dps.find('n:infDPS', NS).get('Id')

    def test_referencia_id(self):
        a = self.assinatura.assinarDPS(self.dps)
        ref = a.find('ds:Signature/ds:SignedInfo/ds:Reference', NS)
        self.assertEqual(ref.get('URI'), '#' + self.id)

    def test_posicao_signature(self):
        a = self.assinatura.assinarDPS(self.dps)
        self.assertEqual([c.tag for c in a],
                         ['{%s}infDPS' % NAMESPACE_NFSE, '{%s}Signature' % DS])

    def test_validacao_xsd(self):
        v = validacao.Validacao()
        r = v.validarDPS(self.assinatura.assinarDPS(self.dps))
        for erro in v.erros:
            print(f"- Linha {erro.line}: {erro.message}")
        self.assertTrue(r)

    def test_mantem_acentos(self):
        a = self.assinatura.assinarDPS(self.dps)
        self.assertEqual(a.findtext('n:infDPS/n:serv/n:cServ/n:xDescServ', namespaces=NS),
                         'Serviço de manutenção de sistemas')

    def _verificar(self, assinado, hashDigest, hashAssinatura):
        """Verifica a assinatura a partir do XML serializado, como a Sefin
        faria, canonicalizando com xml.etree.ElementTree (Python puro), sem
        depender do C14N do libxml2. Para estes documentos (só namespaces
        padrão) o C14N 2.0 do ElementTree produz o mesmo texto do C14N 1.0.
        """
        xml = etree.tostring(assinado, encoding="UTF-8")
        raiz = ET.fromstring(xml)
        signature = raiz.find('{%s}Signature' % DS)
        signedInfo = signature.find('{%s}SignedInfo' % DS)
        c14nInf = c14nTrecho(xml, 'infDPS', NAMESPACE_NFSE)
        c14nSI = c14nTrecho(xml, 'SignedInfo', DS)

        ref = signedInfo.find('{%s}Reference' % DS)
        self.assertEqual(ref.get('URI'), '#' + self.id)
        self.assertEqual(ref.findtext('{%s}DigestValue' % DS),
                         base64.b64encode(hashDigest(c14nInf).digest()).decode())

        _, cert = CertificadoA1(self.certificado).separar_arquivo(self.senha)
        chave = x509.load_pem_x509_certificate(cert.encode()).public_key()
        valor = base64.b64decode(signature.findtext('{%s}SignatureValue' % DS))
        # Levanta InvalidSignature se não conferir
        chave.verify(valor, c14nSI, padding.PKCS1v15(), hashAssinatura())

    def test_verificacao(self):
        self._verificar(self.assinatura.assinarDPS(self.dps),
                        hashlib.sha1, hashes.SHA1)

    def test_verificacao_sha256(self):
        a = assinatura.Assinatura(self.certificado, self.senha, algoritmo="sha256")
        self._verificar(a.assinarDPS(self.dps), hashlib.sha256, hashes.SHA256)

    def test_c14n_igual_ao_python(self):
        a = self.assinatura.assinarDPS(self.dps)
        xml = etree.tostring(a)
        self.assertEqual(self.assinatura._c14n(a.find('n:infDPS', NS)),
                         c14nTrecho(xml, 'infDPS', NAMESPACE_NFSE))
        self.assertEqual(self.assinatura._c14n(a.find('.//ds:SignedInfo', NS)),
                         c14nTrecho(xml, 'SignedInfo', DS))

    def test_sem_xmlns_vazio(self):
        xml = etree.tostring(self.assinatura.assinarDPS(self.dps))
        self.assertNotIn(b'xmlns=""', xml)
        self.assertNotIn(b'ds:', xml)

    def test_nao_altera_original(self):
        self.assinatura.assinarDPS(self.dps)
        self.assertEqual(len(self.dps), 1)

    def test_dps_ja_assinada(self):
        a = self.assinatura.assinarDPS(self.dps)
        with self.assertRaises(Exception):
            self.assinatura.assinarDPS(a)

    def test_dps_sem_id(self):
        self.dps.find('n:infDPS', NS).attrib.pop('Id')
        with self.assertRaises(Exception):
            self.assinatura.assinarDPS(self.dps)


if __name__ == '__main__':
    unittest.main()
