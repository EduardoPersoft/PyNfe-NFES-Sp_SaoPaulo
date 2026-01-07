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
        self.assertEqual(erro, "HTTPSConnectionPool(host='nfews.prefeitura.sp.gov.br', port=443): Max retries exceeded with url: / (Caused by SSLError(SSLError(399, '[SSL: EE_KEY_TOO_SMALL] ee key too small (_ssl.c:3900)')))")

if __name__ == '__main__':
    unittest.main(verbosity=3)
