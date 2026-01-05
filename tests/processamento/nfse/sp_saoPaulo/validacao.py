import unittest
from lxml import etree
from pynfe.processamento.assinatura import AssinaturaA1
from pynfe.processamento.nfse.sp_saoPaulo import assinaturaRPS
from pynfe.processamento.nfse.sp_saoPaulo import serializacao 
from tests.test_nfse_serializacao import SerializacaoNFSeTest

class AssinaturaRPS(unittest.TestCase):

    def setUp(self) -> None:
        self.certificado = "./tests/certificado.pfx"
        self.senha = bytes("123456", encoding="utf-8")
        self.folder = 'pynfe/data/XSDs/NFS-e/sp_saoPaulo/'

    def test_validacao(self):
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        assRPS = assinaturaRPS.Assinatura(
                    caminho_arquivo=self.certificado,
                    senha=self.senha)
        assRPS.assinar(nfse)
        s = serializacao.Serializacao()
        x = s.gerar(nfse)
        ass = AssinaturaA1(self.certificado, self.senha)
        xmlschema_doc = etree.parse(
                f'{self.folder}PedidoEnvioLoteRPS_v02.xsd')
        xmlschema = etree.XMLSchema(xmlschema_doc)
        v = xmlschema.validate(ass.assinarNfse(x))
        for erro in xmlschema.error_log:
            print(f"- Linha {erro.line}: {erro.message}")
        self.assertTrue(v)

    
    

if __name__ == '__main__':
    unittest.main(verbosity=3)
