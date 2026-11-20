import datetime
import re
from lxml import etree
from pynfe.processamento.nfse.nfse_nacional.flags import (
        NAMESPACE_NFSE,
        VERSAO_DPS,
        VERSAO_APLICATIVO,
        TIPO_AMBIENTE_PRODUCAO,
        TIPO_AMBIENTE_HOMOLOGACAO,
        EVENTO_CANCELAMENTO,
        CANCELAMENTO_ERRO_EMISSAO,
        CANCELAMENTO_SERVICO_NAO_PRESTADO,
        CANCELAMENTO_OUTROS,
        )
from pynfe.processamento.nfse.nfse_nacional.serializacao import (
        ErroRegraNegocio,
        dataHoraComFuso,
        )

MOTIVOS_CANCELAMENTO = {
    CANCELAMENTO_ERRO_EMISSAO: "Erro na Emissão",
    CANCELAMENTO_SERVICO_NAO_PRESTADO: "Serviço não Prestado",
    CANCELAMENTO_OUTROS: "Outros",
}


class PedidoEvento(object):
    """Gera o XML do pedido de registro de evento (pedRegEvento) da NFS-e
    Nacional, leiaute 1.01. O XML é gerado sem assinatura."""

    def cancelamento(self, chaveAcesso, autor, motivo, descricao,
                     homologacao=False, dhEvento=None):
        """Pedido de cancelamento da NFS-e (evento 101101).

        - chaveAcesso: chave de acesso da NFS-e (50 dígitos);
        - autor: CNPJ (14 dígitos) ou CPF (11 dígitos) do autor do pedido,
          o prestador que emitiu a NFS-e;
        - motivo: 1 - Erro na Emissão; 2 - Serviço não Prestado; 9 - Outros;
        - descricao: justificativa, de 15 a 255 caracteres;
        - dhEvento: data e hora do pedido; padrão: agora menos um minuto,
          para não ficar posterior ao processamento se o relógio local
          estiver adiantado.
        """
        chave = self._chave(chaveAcesso)
        motivo = int(motivo)
        if motivo not in MOTIVOS_CANCELAMENTO:
            raise ErroRegraNegocio(
                "Motivo de cancelamento inválido: %r (use 1 - Erro na Emissão, "
                "2 - Serviço não Prestado ou 9 - Outros)." % motivo)
        descricao = (descricao or "").strip()
        if not 15 <= len(descricao) <= 255:
            raise ErroRegraNegocio(
                "A justificativa do cancelamento deve ter de 15 a 255 "
                "caracteres (informada com %d)." % len(descricao))

        raiz, info = self._pedido(chave, EVENTO_CANCELAMENTO, autor,
                                  homologacao, dhEvento)
        e = etree.SubElement(info, self._tag("e%d" % EVENTO_CANCELAMENTO))
        etree.SubElement(e, self._tag("xDesc")).text = "Cancelamento de NFS-e"
        etree.SubElement(e, self._tag("cMotivo")).text = str(motivo)
        etree.SubElement(e, self._tag("xMotivo")).text = descricao
        return raiz

    @staticmethod
    def id(chaveAcesso, tipoEvento):
        """Id do pedido (59 posições): "PRE" + chave de acesso (50) + tipo
        do evento (6)."""
        return "PRE%s%06d" % (chaveAcesso, int(tipoEvento))

    def _pedido(self, chave, tipoEvento, autor, homologacao, dhEvento):
        raiz = etree.Element(self._tag("pedRegEvento"), nsmap={None: NAMESPACE_NFSE})
        raiz.set("versao", VERSAO_DPS)
        info = etree.SubElement(raiz, self._tag("infPedReg"))
        info.set("Id", self.id(chave, tipoEvento))
        etree.SubElement(info, self._tag("tpAmb")).text = (
            TIPO_AMBIENTE_HOMOLOGACAO if homologacao else TIPO_AMBIENTE_PRODUCAO)
        etree.SubElement(info, self._tag("verAplic")).text = VERSAO_APLICATIVO
        if dhEvento is None:
            dhEvento = datetime.datetime.now().replace(microsecond=0) \
                - datetime.timedelta(minutes=1)
        etree.SubElement(info, self._tag("dhEvento")).text = dataHoraComFuso(dhEvento)
        documento = re.sub(r"\D", "", str(autor or ""))
        if len(documento) == 14:
            etree.SubElement(info, self._tag("CNPJAutor")).text = documento
        elif len(documento) == 11:
            etree.SubElement(info, self._tag("CPFAutor")).text = documento
        else:
            raise ErroRegraNegocio(
                "O autor do evento deve ser um CNPJ (14 dígitos) ou CPF "
                "(11 dígitos): %r" % autor)
        etree.SubElement(info, self._tag("chNFSe")).text = chave
        return raiz, info

    @staticmethod
    def _chave(chaveAcesso):
        chave = str(chaveAcesso or "").strip()
        if not re.fullmatch(r"[0-9]{50}", chave):
            raise ErroRegraNegocio(
                "A chave de acesso deve ter 50 dígitos: %r" % chaveAcesso)
        return chave

    @staticmethod
    def _tag(nome):
        return "{%s}%s" % (NAMESPACE_NFSE, nome)
