import requests
from pynfe.processamento.nfse.compactador import Compactador
from pynfe.processamento.nfse.nfse_nacional import assinatura
from pynfe.processamento.nfse.nfse_nacional import comunicacao
from pynfe.processamento.nfse.nfse_nacional import resposta
from pynfe.processamento.nfse.nfse_nacional import serializacao
from pynfe.processamento.nfse.nfse_nacional import validacao
from pynfe.processamento.nfse.nfse_nacional.flags import NAMESPACE_NFSE


class ErroComunicacao(Exception):
    """Falha de rede no envio da DPS e não há NFS-e gerada para ela.

    É seguro reenviar a mesma DPS (mesma série e número): a Sefin recusa
    DPS repetida (E0014), então o reenvio não gera NFS-e em duplicidade.
    - idDps: Id da DPS enviada;
    - causa: a exceção original do requests."""

    def __init__(self, idDps, causa):
        self.idDps = idDps
        self.causa = causa
        super().__init__(
            "Falha de comunicação no envio da DPS %s e não há NFS-e gerada "
            "para ela; é seguro reenviar: %s" % (idDps, causa))


class Servicos(object):
    """Ponto de entrada da integração com a Sefin Nacional.

    Os métodos recebem homologacao (padrão False). O mesmo valor define o
    tpAmb da DPS e a URL usada, que precisam coincidir (regra E0006)."""

    def __init__(self, certificado, senha, timeout=60, verificar_ssl=True):
        self._certificado = certificado
        self._senha = senha
        self._timeout = timeout
        self._verificar_ssl = verificar_ssl
        self._assinatura = None
        self._serializacao = serializacao.Serializacao()
        self._validacao = validacao.Validacao()
        self._resposta = resposta.Resposta()
        self._compactador = Compactador()

    def enviar(self, nfse, homologacao=False):
        """Gera, assina, valida e envia a DPS (POST /nfse).

        Devolve um dicionário com chaveAcesso, idDps, nfseXml (str), alertas
        e os dados de processamento. Levanta:
        - serializacao.ErroRegraNegocio se a nota viola uma regra de
          negócio verificável localmente;
        - Exception se a DPS não passar na validação do XSD;
        - resposta.ErroSefin se a Sefin recusar a DPS;
        - ErroComunicacao se houver falha de rede e a NFS-e não tiver sido
          gerada.
        """
        dps = self.gerarDPS(nfse, homologacao)
        idDps = dps.find("{%s}infDPS" % NAMESPACE_NFSE).get("Id")
        com = self._comunicacao(homologacao)
        try:
            r = com.enviarDPS(self._compactador.compactar(dps))
        except (requests.Timeout, requests.ConnectionError) as e:
            return self._recuperar(idDps, e, homologacao)
        return self._resposta.nfse(r, sucesso=(201,))

    def gerarDPS(self, nfse, homologacao=False):
        """Gera, assina e valida a DPS sem enviar. Devolve o
        etree._Element assinado."""
        dps = self._serializacao.gerar(nfse, homologacao=homologacao)
        assinada = self.assinatura.assinarDPS(dps)
        if not self._validacao.validarDPS(assinada):
            raise Exception('Erro na validação da DPS com o XSD:\n' +
                            '\n'.join(f'linha {err.line}: {err.message}'
                                      for err in self._validacao.erros))
        return assinada

    def consultar(self, chaveAcesso, homologacao=False):
        """Consulta a NFS-e pela chave de acesso (GET /nfse/{chave})."""
        r = self._comunicacao(homologacao).consultarNFSe(chaveAcesso)
        return self._resposta.nfse(r, sucesso=(200,))

    def consultarDps(self, idDps, homologacao=False):
        """Chave de acesso da NFS-e gerada a partir da DPS (GET /dps/{id}).
        Levanta resposta.ErroSefin com status 404 se não houver NFS-e."""
        r = self._comunicacao(homologacao).consultarDPS(idDps)
        return self._resposta.dps(r)

    def _recuperar(self, idDps, causa, homologacao):
        """Depois de uma falha de rede no envio, verifica se a NFS-e foi
        gerada. Se foi, devolve-a como se o envio tivesse respondido."""
        try:
            dps = self.consultarDps(idDps, homologacao)
        except resposta.ErroSefin as e:
            if e.status == 404:
                raise ErroComunicacao(idDps, causa) from causa
            raise
        except (requests.Timeout, requests.ConnectionError):
            raise ErroComunicacao(idDps, causa) from causa
        nfse = self.consultar(dps["chaveAcesso"], homologacao)
        nfse["idDps"] = idDps
        nfse["recuperada"] = True
        return nfse

    def _comunicacao(self, homologacao):
        return comunicacao.Comunicacao(self._certificado, self._senha,
                                       homologacao=homologacao,
                                       timeout=self._timeout,
                                       verificar_ssl=self._verificar_ssl)

    @property
    def assinatura(self):
        if self._assinatura is None:
            self._assinatura = assinatura.Assinatura(self._certificado, self._senha)
        return self._assinatura
