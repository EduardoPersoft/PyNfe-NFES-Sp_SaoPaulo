

from pynfe.processamento.nfse import envelope
from pynfe.processamento.nfse.sp_saoPaulo import comunicacao
from pynfe.processamento.nfse.sp_saoPaulo import metodos
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
m = metodos.Metodos()
e = envelope.Envelope()
c = comunicacao.Comunicacao(certificado, senha)
r = c.enviar_lote(e.envelopar(m.enviarLote(x)))
print(r)

