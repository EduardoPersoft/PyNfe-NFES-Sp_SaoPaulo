import unittest
from pynfe.processamento.nfse.sp_saoPaulo import assinaturaRPS
from tests.test_nfse_serializacao import SerializacaoNFSeTest

class AssinaturaRPS(unittest.TestCase):

    def setUp(self) -> None:
        self.certificado = "./tests/certificado.pfx"
        self.senha = bytes("123456", encoding="utf-8")

    def test_string(self):
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        ass = assinaturaRPS.Assinatura(caminho_arquivo=self.certificado,
                                       senha=self.senha)
        self.assertEqual(ass.string(nfse), 
                         self._stringAssinatura())

    def test_assinatura(self):
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        ass = assinaturaRPS.Assinatura(caminho_arquivo=self.certificado,
                                       senha=self.senha)
        self.assertEqual(ass.assinatura(nfse), 
                         "TwQogT4P4i1dNSIPsSWLI6SaiGlo/iN6LVhBaifNaJOMZvaY5Qg7JtJgjUCWGzLAZjbm1a+Ut66K7RU2bZSY4Q4JoiI83tIMzrlRzBOnH3E3LKtgUvD1lV+RVwnCRqGwd+izaHqH91n92tQVM1qgY8sosRny4g9SLbo5Bv56UAg=")

    def test_assinarRPS(self):
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        ass = assinaturaRPS.Assinatura(caminho_arquivo=self.certificado,
                                       senha=self.senha)
        ass.assinar(nfse)
        self.assertEqual(nfse.assinatura, 
                         "TwQogT4P4i1dNSIPsSWLI6SaiGlo/iN6LVhBaifNaJOMZvaY5Qg7JtJgjUCWGzLAZjbm1a+Ut66K7RU2bZSY4Q4JoiI83tIMzrlRzBOnH3E3LKtgUvD1lV+RVwnCRqGwd+izaHqH91n92tQVM1qgY8sosRny4g9SLbo5Bv56UAg=")

    def _stringAssinatura(self):
        insc = '00000000'
        serie = 'A1   '
        numero = '000000000050' 
        emissao = '20250410'
        tributacao = 'T'
        status = 'N'
        issRetido = 'S'
        valor = "000000000001000"
        deducoes = "000000000001000"
        servico = '00101'
        tipoDoc = "2"
        doc = "99999999999999"
        return f"{insc}{serie}{numero}{emissao}{tributacao}{status}{issRetido}{valor}{deducoes}{servico}{tipoDoc}{doc}" 
    
    

if __name__ == '__main__':
    unittest.main(verbosity=3)
