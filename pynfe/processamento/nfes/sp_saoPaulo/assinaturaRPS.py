import base64
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from pynfe.entidades import certificado
from pynfe.processamento.nfes.sp_saoPaulo import tipos

class Assinatura(object):

    def __init__(self, caminho_arquivo=None, senha=None):
        self._pk, self._cert = certificado.CertificadoA1(
                caminho_arquivo=caminho_arquivo).pegarPkCert(senha)

    def assinar(self, nfse):
        nfse.assinatura = self.assinatura(nfse)

    def string(self, nfse):
        self._tipos = tipos.Tipos(nfse)
        insc = nfse.emitente.inscricao_municipal.zfill(8)
        serie = nfse.serie.ljust(5)
        rps = nfse.identificador.zfill(12)
        emissao = nfse.data_emissao.strftime('%Y%m%d')
        tributacao = self._tipos.tributacaoRPS 
        status = 'N'
        issRetido = self._tipos.issRetidoSN
        valor = str(nfse.servico.valor_liquido).replace('.', '').zfill(15)
        deducoes = str(nfse.servico.valor_deducoes).replace('.', '').zfill(15)
        servico = nfse.servico.item_lista.zfill(5)
        tipoDoc = self._tipos.documentoTomador
        doc = nfse.cliente.numero_documento.zfill(14)
        return  f"{insc}{serie}{rps}{emissao}{tributacao}{status}{issRetido}{valor}{deducoes}{servico}{tipoDoc}{doc}"

    def assinatura(self, nfse):
        return base64.b64encode(
                self._pk.sign(
                    self.string(nfse).encode('ASCII'), 
                    padding.PKCS1v15(),
                    hashes.SHA1())).decode('utf-8')

        
