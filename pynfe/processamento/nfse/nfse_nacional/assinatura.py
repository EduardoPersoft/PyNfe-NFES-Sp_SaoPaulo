import base64
import hashlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from lxml import etree
from pynfe.processamento.assinatura import AssinaturaA1
from pynfe.processamento.nfse.nfse_nacional.flags import NAMESPACE_NFSE

DS = "http://www.w3.org/2000/09/xmldsig#"
C14N = "http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
ENVELOPED = DS + "enveloped-signature"

ALGORITMOS = {
    "sha1": (DS + "rsa-sha1", DS + "sha1", hashes.SHA1, hashlib.sha1),
    "sha256": ("http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
               "http://www.w3.org/2001/04/xmlenc#sha256",
               hashes.SHA256, hashlib.sha256),
}


class Assinatura(AssinaturaA1):
    """Assina a DPS da NFS-e Nacional com o certificado A1 (XMLDSIG
    envelopada, C14N inclusivo).

    - A Reference aponta para o Id do infDPS ("#DPS...").
    - A Signature fica como último filho de DPS, depois do infDPS, com o
      namespace do XMLDSIG como padrão (sem prefixo "ds:").
    - Não remove acentos: o XML assinado é o mesmo que foi gerado.

    A assinatura é montada aqui, sem o signxml, porque o C14N inclusivo de
    um trecho do documento está com defeito no libxml2 2.14 (veja _c14n) e
    o signxml depende dele.
    """

    def __init__(self, certificado, senha, algoritmo="sha1"):
        super().__init__(certificado, senha)
        if algoritmo not in ALGORITMOS:
            raise ValueError(f"Algoritmo não suportado: {algoritmo}")
        self._algoritmo = ALGORITMOS[algoritmo]

    def assinarDPS(self, dps: etree._Element) -> etree._Element:
        # Trabalha sobre uma cópia limpa, igual ao que será enviado.
        dps = etree.fromstring(etree.tostring(dps))
        infDPS = dps.find("{%s}infDPS" % NAMESPACE_NFSE)
        if infDPS is None or not infDPS.get("Id"):
            raise Exception("DPS sem infDPS com o atributo Id.")
        if dps.find("{%s}Signature" % DS) is not None:
            raise Exception("DPS já assinada.")

        metodo, metodoDigest, hashAssinatura, hashDigest = self._algoritmo

        digest = base64.b64encode(
            hashDigest(self._c14n(infDPS)).digest()).decode("ascii")

        signature = etree.SubElement(dps, self._ds("Signature"), nsmap={None: DS})
        signedInfo = etree.SubElement(signature, self._ds("SignedInfo"))
        etree.SubElement(signedInfo, self._ds("CanonicalizationMethod"), Algorithm=C14N)
        etree.SubElement(signedInfo, self._ds("SignatureMethod"), Algorithm=metodo)
        reference = etree.SubElement(signedInfo, self._ds("Reference"),
                                     URI="#%s" % infDPS.get("Id"))
        transforms = etree.SubElement(reference, self._ds("Transforms"))
        etree.SubElement(transforms, self._ds("Transform"), Algorithm=ENVELOPED)
        etree.SubElement(transforms, self._ds("Transform"), Algorithm=C14N)
        etree.SubElement(reference, self._ds("DigestMethod"), Algorithm=metodoDigest)
        etree.SubElement(reference, self._ds("DigestValue")).text = digest

        valor = self._chavePrivada.sign(self._c14n(signedInfo),
                                        padding.PKCS1v15(), hashAssinatura())
        etree.SubElement(signature, self._ds("SignatureValue")).text = \
            base64.b64encode(valor).decode("ascii")

        keyInfo = etree.SubElement(signature, self._ds("KeyInfo"))
        x509Data = etree.SubElement(keyInfo, self._ds("X509Data"))
        etree.SubElement(x509Data, self._ds("X509Certificate")).text = self._certificadoBase64
        return dps

    @staticmethod
    def _ds(nome):
        return "{%s}%s" % (DS, nome)

    @staticmethod
    def _c14n(elemento):
        """C14N inclusivo do elemento, calculado sobre uma cópia que é a
        raiz do documento.

        O C14N inclusivo de um trecho do documento no libxml2 2.14 (usado
        pelo lxml) acrescenta xmlns="" em elementos que herdam o namespace
        padrão de um ancestral, o que não é C14N correto e faria a Sefin
        recusar a assinatura. Com a cópia como raiz o resultado é correto.
        A cópia declara na raiz os namespaces herdados que são usados; na
        DPS os únicos são os namespaces padrão da NFS-e (infDPS) e do
        XMLDSIG (SignedInfo), então o resultado é igual ao C14N inclusivo do
        trecho.
        """
        copia = etree.fromstring(etree.tostring(elemento))
        return etree.tostring(copia, method="c14n", exclusive=False,
                              with_comments=False)

    @property
    def _chavePrivada(self):
        chave = self.key if isinstance(self.key, bytes) else self.key.encode()
        return serialization.load_pem_private_key(chave, password=None)

    @property
    def _certificadoBase64(self):
        cert = self.cert if isinstance(self.cert, str) else self.cert.decode()
        return "".join(linha for linha in cert.strip().splitlines()
                       if not linha.startswith("-----"))
