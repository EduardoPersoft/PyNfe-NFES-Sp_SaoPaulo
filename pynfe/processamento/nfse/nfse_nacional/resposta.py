from pynfe.processamento.nfse.compactador import Compactador


class ErroSefin(Exception):
    """A Sefin Nacional recusou a requisição ou respondeu com erro.

    - status: código HTTP;
    - erros: lista de dicionários com codigo, descricao e complemento;
    - idDps: Id da DPS, quando a Sefin conseguiu lê-lo;
    - texto: corpo da resposta, como veio da Sefin.
    """

    def __init__(self, status, erros=None, idDps=None, texto=None):
        self.status = status
        self.erros = erros or []
        self.idDps = idDps
        self.texto = texto
        if any(e.get("codigo") or e.get("descricao") for e in self.erros):
            detalhe = "\n".join(
                "%s %s%s" % (e.get("codigo") or "", e.get("descricao") or "",
                             " (%s)" % e["complemento"] if e.get("complemento") else "")
                for e in self.erros)
        else:
            detalhe = (texto or "").strip()[:500] or "resposta sem conteúdo"
        super().__init__("Sefin Nacional, HTTP %s:\n%s" % (status, detalhe))

    @property
    def codigos(self):
        return [e.get("codigo") for e in self.erros]


class Resposta(object):
    """Interpreta as respostas JSON da Sefin Nacional.

    Os métodos devolvem dicionários em caso de sucesso e levantam ErroSefin
    nos demais casos. A API usa dois formatos de erro: NFSePostResponseErro
    (lista "erros", só no POST /nfse) e ResponseErro (objeto "erro"); os
    dois são tratados aqui."""

    def __init__(self):
        self._compactador = Compactador()

    def nfse(self, response, sucesso=(200, 201)):
        """Resposta do POST /nfse (201) ou do GET /nfse/{chave} (200)."""
        dados = self._json(response, sucesso)
        r = self._cabecalho(dados)
        r["chaveAcesso"] = dados.get("chaveAcesso")
        r["idDps"] = dados.get("idDps")
        r["nfseXml"] = self._compactador.descompactar(dados["nfseXmlGZipB64"])
        r["alertas"] = self._mensagens(dados.get("alertas"))
        return r

    def dps(self, response):
        """Resposta do GET /dps/{id} (200)."""
        dados = self._json(response, (200,))
        r = self._cabecalho(dados)
        r["idDps"] = dados.get("idDps")
        r["chaveAcesso"] = dados.get("chaveAcesso")
        return r

    def evento(self, response, sucesso=(200, 201)):
        """Resposta do registro (201) ou da consulta (200) de evento."""
        dados = self._json(response, sucesso)
        r = self._cabecalho(dados)
        r["eventoXml"] = self._compactador.descompactar(dados["eventoXmlGZipB64"])
        return r

    @staticmethod
    def _cabecalho(dados):
        return {
            "tipoAmbiente": dados.get("tipoAmbiente"),
            "versaoAplicativo": dados.get("versaoAplicativo"),
            "dataHoraProcessamento": dados.get("dataHoraProcessamento"),
        }

    @staticmethod
    def _mensagens(lista):
        """Normaliza as mensagens de erro ou alerta. As chaves são lidas sem
        diferenciar maiúsculas: o swagger.json usa "codigo", mas a Sefin
        também responde "Codigo"."""
        if not lista:
            return []
        if isinstance(lista, dict):
            lista = [lista]
        mensagens = []
        for m in lista:
            if not isinstance(m, dict):
                m = {"descricao": str(m)}
            m = {str(k).lower(): v for k, v in m.items()}
            mensagens.append({"codigo": m.get("codigo"),
                              "descricao": m.get("descricao"),
                              "complemento": m.get("complemento")})
        return mensagens

    def _json(self, response, sucesso):
        try:
            dados = response.json()
        except ValueError:
            dados = None
        if response.status_code in sucesso and isinstance(dados, dict):
            return dados
        if not isinstance(dados, dict):
            raise ErroSefin(response.status_code, texto=response.text)
        erros = self._mensagens(dados.get("erros") or dados.get("erro"))
        raise ErroSefin(response.status_code, erros=erros,
                        idDps=dados.get("idDPS") or dados.get("idDps"),
                        texto=response.text)
