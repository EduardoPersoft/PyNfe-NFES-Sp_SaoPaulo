import unittest
from pynfe.processamento.nfse.sp_saoPaulo import assinaturaRPS
from tests.test_nfse_serializacao import SerializacaoNFSeTest

class AssinaturaRPS(unittest.TestCase):

    def setUp(self) -> None:
        self.certificado = "./tests/certificado.pfx"
        self.senha = bytes("123456", encoding="utf-8")

    def test_string(self):
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        nfse.simples = 2
        ass = assinaturaRPS.Assinatura(caminho_arquivo=self.certificado,
                                       senha=self.senha)
        self.assertEqual(ass.string(nfse), 
                         self._stringAssinatura())

    def test_assinatura(self):
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        nfse.simples = 2
        ass = assinaturaRPS.Assinatura(caminho_arquivo=self.certificado,
                                       senha=self.senha)
        self.assertEqual(ass.assinatura(nfse), 
                         "W4hY36UBu5ts4p+f9+R/TEA+p5F03RoVsm4WTW6cOQD7cdfVrgUuEXJpHfE0JRg0JgcweALHcxyJquhIvO9t9OHQ/ZeiwyUSjenlOL68dFfOra2RH5uiMKW92/fnsCpX12hp38jKu0RuQfW19IWpIqrn3iCrpRddt3V/y2ue0iY=")

    def test_assinarRPS(self):
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        nfse.simples = 2
        ass = assinaturaRPS.Assinatura(caminho_arquivo=self.certificado,
                                       senha=self.senha)
        ass.assinar(nfse)
        self.assertEqual(nfse.assinatura, 
                         "W4hY36UBu5ts4p+f9+R/TEA+p5F03RoVsm4WTW6cOQD7cdfVrgUuEXJpHfE0JRg0JgcweALHcxyJquhIvO9t9OHQ/ZeiwyUSjenlOL68dFfOra2RH5uiMKW92/fnsCpX12hp38jKu0RuQfW19IWpIqrn3iCrpRddt3V/y2ue0iY=")

    def test_stringSimples(self):
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        ass = assinaturaRPS.Assinatura(caminho_arquivo=self.certificado,
                                       senha=self.senha)
        self.assertEqual(ass.string(nfse), 
                         self._stringAssinaturaSimples())

    def test_assinaturaSimples(self):
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        ass = assinaturaRPS.Assinatura(caminho_arquivo=self.certificado,
                                       senha=self.senha)
        self.assertEqual(ass.assinatura(nfse), 
                         "aFNza36jjKBT3qBFKMibs68yiJYwGz9B4MIqljrY1VPu1vkQGpc3hK19140MKSo/vRKz+KqZYmt6/kzQnuDNvUVhYs7rl5Na7Haxq9z3bbgm68siWFHVE2TpvsfrrygznGQyivloLPxmZk0JmQ+nb2GtZv4EoiqR5w7Gq4gky7c=")


    def test_assinarRPSSimples(self):
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        ass = assinaturaRPS.Assinatura(caminho_arquivo=self.certificado,
                                       senha=self.senha)
        ass.assinar(nfse)
        self.assertEqual(nfse.assinatura, 
                         "aFNza36jjKBT3qBFKMibs68yiJYwGz9B4MIqljrY1VPu1vkQGpc3hK19140MKSo/vRKz+KqZYmt6/kzQnuDNvUVhYs7rl5Na7Haxq9z3bbgm68siWFHVE2TpvsfrrygznGQyivloLPxmZk0JmQ+nb2GtZv4EoiqR5w7Gq4gky7c=")

    def _stringAssinatura(self):
        insc = '000000000000'
        serie = 'A1   '
        numero = '000000000050' 
        emissao = '20250410'
        tributacao = 'T'
        status = 'N'
        issRetido = 'S'
        valor = "000000000001000"
        deducoes = "000000000001000"
        servico = '01234'
        tipoDoc = "2"
        doc = "99999999999999"
        return f"{insc}{serie}{numero}{emissao}{tributacao}{status}{issRetido}{valor}{deducoes}{servico}{tipoDoc}{doc}" 
    
    def _stringAssinaturaSimples(self):
        insc = '00000000'
        serie = 'A1   '
        numero = '000000000050' 
        emissao = '20250410'
        tributacao = 'T'
        status = 'N'
        issRetido = 'S'
        valor = "000000000001000"
        deducoes = "000000000001000"
        servico = '01234'
        tipoDoc = "2"
        doc = "99999999999999"
        return f"{insc}{serie}{numero}{emissao}{tributacao}{status}{issRetido}{valor}{deducoes}{servico}{tipoDoc}{doc}" 
    
    

if __name__ == '__main__':
    unittest.main(verbosity=3)
