import unittest
from pynfe.processamento.assinatura import AssinaturaA1
from pynfe.processamento.nfse.sp_saoPaulo import assinaturaRPS
from pynfe.processamento.nfse.sp_saoPaulo import serializacao 
from pynfe.processamento.nfse.sp_saoPaulo import validacao 
from tests.test_nfse_serializacao import SerializacaoNFSeTest

class AssinaturaRPS(unittest.TestCase):

    def setUp(self) -> None:
        self.certificado = "./tests/certificado.pfx"
        self.senha = bytes("123456", encoding="utf-8")

    def test_validacao(self):
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        assRPS = assinaturaRPS.Assinatura(
                    caminho_arquivo=self.certificado,
                    senha=self.senha)
        assRPS.assinar(nfse)
        s = serializacao.Serializacao()
        x = s.gerar(nfse)
        ass = AssinaturaA1(self.certificado, self.senha)
        v = validacao.Validacao()
        r = v.validarLote(ass.assinarNfse(x))
        for erro in v.erros:
            print(f"- Linha {erro.line}: {erro.message}")
        self.assertTrue(r)

    
    

if __name__ == '__main__':
    unittest.main(verbosity=3)
