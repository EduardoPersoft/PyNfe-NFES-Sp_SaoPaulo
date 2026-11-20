import unittest
from pynfe.processamento.nfse.sp_saoPaulo import servicos
from tests.test_nfse_serializacao import SerializacaoNFSeTest

class Servico(unittest.TestCase):

    def test_enviarLote(self):
        certificado="./tests/certificado.pfx"
        certificadoSenha=bytes("123456", "utf-8")
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        nfse.simples = 2
        s = servicos.Servicos(certificado, certificadoSenha)
        erro = ""
        try:
            s.enviarLote(nfse)
        except Exception as e:
            erro = str(e)
        self.assertEqual(erro[0:19], "HTTPSConnectionPool")

    def test_enviarLoteSimples(self):
        certificado="./tests/certificado.pfx"
        certificadoSenha=bytes("123456", "utf-8")
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        s = servicos.Servicos(certificado, certificadoSenha)
        erro = ""
        try:
            s.enviarLote(nfse)
        except Exception as e:
            erro = str(e)
        self.assertEqual(erro[0:19], "HTTPSConnectionPool")


if __name__ == '__main__':
    unittest.main(verbosity=3)
