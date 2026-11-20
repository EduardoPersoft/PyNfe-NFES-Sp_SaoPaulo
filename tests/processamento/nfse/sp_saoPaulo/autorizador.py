import unittest
from pynfe.processamento.nfse import autorizador
from tests.test_nfse_serializacao import SerializacaoNFSeTest

class Autorizador(unittest.TestCase):

    def test_autorizador(self):
        certificado="./tests/certificado.pfx"
        senha=bytes("123456", "utf-8")
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        s = autorizador.get('3550308', certificado, senha)
        erro = ""
        try:
            s.enviarLote(nfse)
        except Exception as e:
            erro = str(e)
        self.assertEqual(erro[0:19], "HTTPSConnectionPool")

if __name__ == '__main__':
    unittest.main(verbosity=3)
