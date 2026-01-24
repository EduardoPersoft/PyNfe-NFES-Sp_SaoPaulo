from lxml import etree
import xmltodict
from pynfe.processamento import assinatura
from pynfe.processamento.nfse.sp_saoPaulo import assinaturaRPS
from pynfe.processamento.nfse.sp_saoPaulo import serializacao 
from pynfe.processamento.nfse.sp_saoPaulo import metodos
from pynfe.processamento.nfse.sp_saoPaulo import comunicacao
from pynfe.processamento.nfse.sp_saoPaulo import validacao
from pynfe.processamento.nfse import envelope

class Servicos(object):

    def __init__(self, certificado, senha):
        self._certificado=certificado
        self._senha = senha
        self._assinaturaRPS = None
        self._assinatura = None
        self._serializacao = None
        self._envelope = None
        self._metodos = None
        self._comunicacao = None
        self._validacao = None

    def enviarLote(self, nfse, homologacao=False):
        self._homologacao = homologacao
        self.assinarRPS(nfse)
        s = self.serializar(nfse)
        a = self.assinatura.assinarNfse(s)
        self.validacao.validarLote(a)
        e = self.enveloparEnviarLote(a, homologacao=homologacao) 
        return self._getResultado(self.comunicacao.enviar_lote(
            e).text, homologacao)

    def setSchema(self, value):
        self.validacao.setSchema(value)
        self.metodos.setSchema(value)


    def _getResultado(self, retorno, homologacao):
        evento = "EnvioLoteRPSResponse"
        if homologacao:
            evento = "TesteEnvioLoteRPSResponse"
        corpo = xmltodict.parse(retorno)['soap:Envelope']['soap:Body']
        retorno = xmltodict.parse(corpo[evento]["RetornoXML"])
        return retorno


    def assinarRPS(self, nfse):
        if isinstance(nfse, list):
            for n in nfse:
                self.assinaturaRPS.assinar(n)
            return None
        self.assinaturaRPS.assinar(nfse)

    def serializar(self, nfse):
        return self.serializacao.gerar(nfse)

    def enveloparEnviarLote(self, nfseSerializada, homologacao=False):
        return self.envelope.envelopar(
                self.metodos.enviarLote(nfseSerializada,
                                        homologacao=homologacao))

    @property
    def assinaturaRPS(self):
        if self._assinaturaRPS:
            return self._assinaturaRPS
        self._assinaturaRPS = assinaturaRPS.Assinatura(
                self._certificado, self._senha) 
        return self._assinaturaRPS

    @property
    def  serializacao(self):
        if self._serializacao:
            return self._serializacao
        self._serializacao = serializacao.Serializacao()
        return self._serializacao
    
    @property
    def envelope(self):
        if self._envelope:
            return self._envelope
        self._envelope = envelope.Envelope()
        return self._envelope

    @property
    def validacao(self):
        if self._validacao:
            return self._validacao
        self._validacao = validacao.Validacao()
        return self._validacao

    @property
    def metodos(self):
        if self._metodos:
            return self._metodos
        self._metodos = metodos.Metodos()
        return self._metodos

    @property
    def comunicacao(self):
        if self._comunicacao:
            return self._comunicacao
        self._comunicacao = comunicacao.Comunicacao(self._certificado,
                                                    self._senha,
                                                    homologacao=self._homologacao)
        return self._comunicacao

    @property
    def assinatura(self):
        if self._assinatura:
            return self._assinatura
        self._assinatura = assinatura.AssinaturaA1(self._certificado,
                                                   self._senha)
        return self._assinatura
