
from pynfe.processamento.assinatura import AssinaturaA1
from pynfe.processamento.nfse.sp_saoPaulo import assinaturaRPS
from pynfe.processamento.nfse.sp_saoPaulo import serializacao 
from tests.test_nfse_serializacao import SerializacaoNFSeTest

certificado = "./tests/certificado.pfx"
senha = bytes("123456", encoding="utf-8")
nfse = SerializacaoNFSeTest.get_notafiscal_servico()
assRPS = assinaturaRPS.Assinatura(
        caminho_arquivo=certificado,
        senha=senha)
assRPS.assinar(nfse)
s = serializacao.Serializacao()
x = s.gerar(nfse)
ass = AssinaturaA1(certificado, senha)
print(ass.assinarNfse(xml=x,retorna_string=True))

