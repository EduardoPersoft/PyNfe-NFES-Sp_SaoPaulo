import re
import requests
from pynfe.entidades.certificado import CertificadoA1
from pynfe.processamento.nfse.nfse_nacional.flags import (
        URL_PRODUCAO,
        URL_HOMOLOGACAO,
        )


class Comunicacao(object):
    """Requisições à API da Sefin Nacional (JSON por HTTPS com autenticação
    mútua pelo certificado A1).

    Cada método devolve o requests.Response sem interpretar; quem interpreta
    é o resposta.py. Erros de rede (timeout, conexão) são propagados como
    exceções do requests.

    verificar_ssl é repassado ao requests (verify): True usa as autoridades
    certificadoras do certifi; também pode ser o caminho de um arquivo de
    cadeia de certificados, caso o servidor use uma cadeia que o certifi
    não reconhece.
    """

    def __init__(self, certificado, senha, homologacao=False, timeout=60,
                 verificar_ssl=True):
        self._certificado = certificado
        self._senha = senha
        self._homologacao = homologacao
        self._timeout = timeout
        self._verificar_ssl = verificar_ssl

    @property
    def url(self):
        if self._homologacao:
            return URL_HOMOLOGACAO
        return URL_PRODUCAO

    def enviarDPS(self, dpsXmlGZipB64):
        """POST /nfse: envia a DPS e gera a NFS-e de forma síncrona."""
        return self._requisicao("POST", "/nfse",
                                json={"dpsXmlGZipB64": dpsXmlGZipB64})

    def consultarNFSe(self, chaveAcesso):
        """GET /nfse/{chaveAcesso}"""
        return self._requisicao("GET", "/nfse/%s" % self._chave(chaveAcesso))

    def consultarDPS(self, idDps):
        """GET /dps/{id}: chave de acesso da NFS-e gerada a partir da DPS."""
        return self._requisicao("GET", "/dps/%s" % self._idDps(idDps))

    def existeDPS(self, idDps):
        """HEAD /dps/{id}"""
        return self._requisicao("HEAD", "/dps/%s" % self._idDps(idDps))

    def registrarEvento(self, chaveAcesso, pedidoRegistroEventoXmlGZipB64):
        """POST /nfse/{chaveAcesso}/eventos"""
        return self._requisicao(
            "POST", "/nfse/%s/eventos" % self._chave(chaveAcesso),
            json={"pedidoRegistroEventoXmlGZipB64": pedidoRegistroEventoXmlGZipB64})

    def consultarEvento(self, chaveAcesso, tipoEvento, numSeqEvento):
        """GET /nfse/{chaveAcesso}/eventos/{tipoEvento}/{numSeqEvento}"""
        return self._requisicao(
            "GET", "/nfse/%s/eventos/%d/%d" % (self._chave(chaveAcesso),
                                               int(tipoEvento), int(numSeqEvento)))

    @staticmethod
    def _chave(chaveAcesso):
        chave = str(chaveAcesso).strip()
        if not re.fullmatch(r"[0-9]{50}", chave):
            raise ValueError("A chave de acesso deve ter 50 dígitos: %r" % chaveAcesso)
        return chave

    @staticmethod
    def _idDps(idDps):
        id_ = str(idDps).strip()
        if not re.fullmatch(r"DPS[0-9]{42}", id_):
            raise ValueError("Id de DPS inválido: %r" % idDps)
        return id_

    def _requisicao(self, metodo, caminho, json=None):
        certificado = CertificadoA1(self._certificado)
        chave, cert = certificado.separar_arquivo(self._senha, caminho=True)
        try:
            return requests.request(
                metodo,
                self.url + caminho,
                json=json,
                headers={"Accept": "application/json"},
                cert=(cert, chave),
                verify=self._verificar_ssl,
                timeout=self._timeout,
            )
        finally:
            certificado.excluir()
