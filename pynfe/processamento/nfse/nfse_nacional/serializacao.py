import datetime
import decimal
import re
from lxml import etree
from pynfe.processamento.nfse.nfse_nacional.flags import (
        NAMESPACE_NFSE,
        VERSAO_DPS,
        VERSAO_APLICATIVO,
        FUSO_HORARIO_PADRAO,
        TIPO_AMBIENTE_PRODUCAO,
        TIPO_AMBIENTE_HOMOLOGACAO,
        EMITENTE_PRESTADOR,
        SIMPLES_NAO_OPTANTE,
        SIMPLES_ME_EPP,
        TIPO_INSCRICAO_CPF,
        TIPO_INSCRICAO_CNPJ,
        )


class Serializacao(object):
    """Gera o XML da DPS (Declaração de Prestação de Serviços) no leiaute
    1.01 da NFS-e Nacional a partir de um NotaFiscalServico.

    O XML é gerado sem assinatura."""

    def gerar(self, nfse, homologacao=False):
        return DPS(nfse, homologacao).element


def _somenteNumeros(value):
    return re.sub(r'\D', '', str(value or ''))


def _vazio(value):
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (int, float, decimal.Decimal)) and not isinstance(value, bool):
        return value == 0
    return False


class Elemento(object):

    def __init__(self, nfse):
        self._nfse = nfse
        self._element = self._getRaiz()

    @property
    def element(self):
        return self._element

    def _getRaiz(self) -> etree.Element:
        pass

    @staticmethod
    def _tag(nome):
        return "{%s}%s" % (NAMESPACE_NFSE, nome)

    def _sub(self, nome, raiz=None):
        if raiz is None:
            raiz = self._element
        return etree.SubElement(raiz, self._tag(nome))

    def _add(self, nome, value, raiz=None):
        if isinstance(value, decimal.Decimal) or isinstance(value, float):
            value = '%.2f' % value
        elif isinstance(value, datetime.date):
            value = value.strftime('%Y-%m-%d')
        elif not isinstance(value, str):
            value = str(value)
        self._sub(nome, raiz).text = value

    def _addOpcional(self, nome, value, raiz=None):
        if not _vazio(value):
            self._add(nome, value, raiz)

    def _documento(self, tipo, numero, raiz):
        """CNPJ ou CPF, conforme o tipo ou o tamanho do número."""
        numero = _somenteNumeros(numero)
        if tipo == 'CPF' or (tipo is None and len(numero) == 11):
            self._add('CPF', numero, raiz)
        else:
            self._add('CNPJ', numero, raiz)


class DPS(Elemento):

    def __init__(self, nfse, homologacao=False):
        self._homologacao = homologacao
        super().__init__(nfse)
        self._element.append(InfDPS(nfse, homologacao).element)

    def _getRaiz(self):
        r = etree.Element(self._tag("DPS"), nsmap={None: NAMESPACE_NFSE})
        r.set("versao", VERSAO_DPS)
        return r


class InfDPS(Elemento):

    def __init__(self, nfse, homologacao=False):
        self._homologacao = homologacao
        super().__init__(nfse)
        self._add("tpAmb", self._tpAmb)
        self._add("dhEmi", self._dhEmi)
        self._add("verAplic", VERSAO_APLICATIVO)
        self._add("serie", self._serie)
        self._add("nDPS", self._nDPS)
        self._add("dCompet", self._dCompet)
        self._add("tpEmit", self._tpEmit)
        self._add("cLocEmi", self._cLocEmi)
        self._element.append(Prestador(nfse).element)
        if getattr(nfse, 'cliente', None) is not None:
            self._element.append(Tomador(nfse).element)
        self._element.append(Servico(nfse).element)
        self._element.append(Valores(nfse).element)
        if not _vazio(getattr(nfse, 'IBSCBS_cIndOp', None)):
            self._element.append(IBSCBS(nfse).element)

    def _getRaiz(self):
        r = etree.Element(self._tag("infDPS"))
        r.set("Id", self.id)
        return r

    @property
    def id(self):
        """Id da DPS (45 posições): "DPS" + código do município emissor (7)
        + tipo de inscrição federal (1) + inscrição federal (14) + série (5)
        + número da DPS (15)."""
        documento = _somenteNumeros(self._nfse.emitente.cnpj)
        tipo = TIPO_INSCRICAO_CPF if len(documento) == 11 else TIPO_INSCRICAO_CNPJ
        return "DPS%s%s%s%s%s" % (self._cLocEmi.zfill(7),
                                  tipo,
                                  documento.zfill(14),
                                  self._serie.zfill(5),
                                  self._nDPS.zfill(15))

    @property
    def _tpAmb(self):
        if self._homologacao:
            return TIPO_AMBIENTE_HOMOLOGACAO
        return TIPO_AMBIENTE_PRODUCAO

    @property
    def _dhEmi(self):
        d = self._nfse.data_emissao
        texto = d.strftime('%Y-%m-%dT%H:%M:%S')
        if d.tzinfo is None or d.utcoffset() is None:
            return texto + FUSO_HORARIO_PADRAO
        minutos = int(d.utcoffset().total_seconds() // 60)
        sinal = '-' if minutos < 0 else '+'
        minutos = abs(minutos)
        return "%s%s%02d:%02d" % (texto, sinal, minutos // 60, minutos % 60)

    @property
    def _serie(self):
        return str(self._nfse.serie).strip()

    @property
    def _nDPS(self):
        return str(int(_somenteNumeros(self._nfse.identificador)))

    @property
    def _dCompet(self):
        d = getattr(self._nfse, 'data_competencia', None) or self._nfse.data_emissao
        return d.strftime('%Y-%m-%d')

    @property
    def _tpEmit(self):
        return getattr(self._nfse, 'tipo_emitente', None) or EMITENTE_PRESTADOR

    @property
    def _cLocEmi(self):
        return _somenteNumeros(self._nfse.emitente.endereco_cod_municipio)


class Prestador(Elemento):

    def __init__(self, nfse):
        super().__init__(nfse)
        emitente = nfse.emitente
        self._documento(None, emitente.cnpj, self._element)
        self._addOpcional("IM", emitente.inscricao_municipal)
        # Quando o emitente da DPS é o próprio prestador, nome e endereço
        # vêm do cadastro nacional e não devem ser informados.
        if self._tpEmit != EMITENTE_PRESTADOR:
            self._add("xNome", emitente.razao_social)
            self._element.append(Endereco(emitente).element)
        self._addOpcional("fone", _somenteNumeros(emitente.endereco_telefone))
        self._addOpcional("email", getattr(emitente, 'email', None))
        self._element.append(self._regTrib)

    def _getRaiz(self):
        return etree.Element(self._tag("prest"))

    @property
    def _tpEmit(self):
        return getattr(self._nfse, 'tipo_emitente', None) or EMITENTE_PRESTADOR

    @property
    def _opSimpNac(self):
        op = getattr(self._nfse, 'op_simples_nacional', None)
        if op:
            return op
        if self._nfse.simples == 1:
            return SIMPLES_ME_EPP
        return SIMPLES_NAO_OPTANTE

    @property
    def _regTrib(self):
        r = etree.Element(self._tag("regTrib"))
        op = self._opSimpNac
        self._add("opSimpNac", op, r)
        regAp = getattr(self._nfse, 'regime_apuracao_sn', None)
        if regAp is None and op == SIMPLES_ME_EPP:
            regAp = 1
        if regAp:
            self._add("regApTribSN", regAp, r)
        self._add("regEspTrib", getattr(self._nfse, 'regime_especial', None) or 0, r)
        return r


class Endereco(Elemento):
    """Endereço nacional (TCEndereco/endNac) de um emitente ou cliente."""

    def __init__(self, pessoa):
        self._pessoa = pessoa
        super().__init__(None)
        nac = self._sub("endNac")
        self._add("cMun", _somenteNumeros(pessoa.endereco_cod_municipio), nac)
        self._add("CEP", _somenteNumeros(pessoa.endereco_cep), nac)
        self._add("xLgr", pessoa.endereco_logradouro)
        self._add("nro", pessoa.endereco_numero or "S/N")
        self._addOpcional("xCpl", pessoa.endereco_complemento)
        self._add("xBairro", pessoa.endereco_bairro)

    def _getRaiz(self):
        return etree.Element(self._tag("end"))


class Tomador(Elemento):

    def __init__(self, nfse):
        super().__init__(nfse)
        cliente = nfse.cliente
        self._documento(cliente.tipo_documento, cliente.numero_documento,
                        self._element)
        self._addOpcional("IM", cliente.inscricao_municipal)
        self._add("xNome", cliente.razao_social)
        if not _vazio(cliente.endereco_logradouro):
            self._element.append(Endereco(cliente).element)
        self._addOpcional("fone", _somenteNumeros(cliente.endereco_telefone))
        self._addOpcional("email", cliente.email)

    def _getRaiz(self):
        return etree.Element(self._tag("toma"))


class Servico(Elemento):

    def __init__(self, nfse):
        super().__init__(nfse)
        servico = nfse.servico
        loc = self._sub("locPrest")
        self._add("cLocPrestacao", self._cLocPrestacao, loc)
        c = self._sub("cServ")
        self._add("cTribNac", _somenteNumeros(servico.codigo_tributacao_nacional), c)
        self._addOpcional("cTribMun",
                          getattr(servico, 'codigo_tributacao_municipal_nacional', None), c)
        self._add("xDescServ", servico.discriminacao, c)
        self._addOpcional("cNBS", _somenteNumeros(getattr(servico, 'nbs', None)), c)

    def _getRaiz(self):
        return etree.Element(self._tag("serv"))

    @property
    def _cLocPrestacao(self):
        servico = self._nfse.servico
        cod = getattr(servico, 'codigo_municipio', None)
        if _vazio(cod):
            cod = self._nfse.emitente.endereco_cod_municipio
        return _somenteNumeros(cod)


class Valores(Elemento):

    def __init__(self, nfse):
        super().__init__(nfse)
        servico = nfse.servico
        v = self._sub("vServPrest")
        self._add("vServ", decimal.Decimal(servico.valor_servico), v)
        self._descontos(servico)
        self._element.append(self._trib)

    def _getRaiz(self):
        return etree.Element(self._tag("valores"))

    def _descontos(self, servico):
        incond = getattr(servico, 'desconto_incondicionado', None)
        cond = getattr(servico, 'desconto_condicionado', None)
        if _vazio(incond) and _vazio(cond):
            return
        d = self._sub("vDescCondIncond")
        self._addOpcional("vDescIncond", incond, d)
        self._addOpcional("vDescCond", cond, d)

    @property
    def _trib(self):
        servico = self._nfse.servico
        t = etree.Element(self._tag("trib"))
        m = self._sub("tribMun", t)
        self._add("tribISSQN", getattr(servico, 'tributacao_issqn', None) or 1, m)
        self._add("tpRetISSQN", self._tpRetISSQN, m)
        self._addOpcional("pAliq", getattr(servico, 'aliquota', None), m)
        self._tribFed(t)
        self._totTrib(t)
        return t

    @property
    def _tpRetISSQN(self):
        """1 - Não retido; 2 - Retido pelo tomador; 3 - Retido pelo
        intermediário. iss_retido segue o padrão 1-Sim; 2-Não."""
        tp = getattr(self._nfse.servico, 'tipo_retencao_issqn', None)
        if tp:
            return tp
        if self._nfse.servico.iss_retido == 1:
            return 2
        return 1

    def _tribFed(self, raiz):
        servico = self._nfse.servico
        retencoes = [("vRetCP", getattr(servico, 'valor_inss', None)),
                     ("vRetIRRF", getattr(servico, 'valor_ir', None)),
                     ("vRetCSLL", getattr(servico, 'valor_csll', None))]
        if all(_vazio(v) for _, v in retencoes):
            return
        f = self._sub("tribFed", raiz)
        for nome, valor in retencoes:
            self._addOpcional(nome, valor, f)

    def _totTrib(self, raiz):
        """Por enquanto informa pTotTribSN quando houver o percentual do
        Simples Nacional; caso contrário indTotTrib = 0 (não informar)."""
        tot = self._sub("totTrib", raiz)
        pSN = getattr(self._nfse, 'percentual_tributos_sn', None)
        if not _vazio(pSN):
            self._add("pTotTribSN", pSN, tot)
        else:
            self._add("indTotTrib", 0, tot)


class IBSCBS(Elemento):

    def __init__(self, nfse):
        super().__init__(nfse)
        self._add("finNFSe", getattr(nfse, 'IBSCBS_finNFSe', None) or 0)
        indFinal = getattr(nfse, 'IBSCBS_indFinal', None)
        if indFinal is not None:
            self._add("indFinal", indFinal)
        self._add("cIndOp", nfse.IBSCBS_cIndOp)
        self._addOpcional("tpOper", getattr(nfse, 'IBSCBS_tpOper', None))
        self._add("indDest", getattr(nfse, 'IBSCBS_indDest', None) or 0)
        v = self._sub("valores")
        t = self._sub("trib", v)
        g = self._sub("gIBSCBS", t)
        self._add("CST", nfse.IBSCBS_CST, g)
        self._add("cClassTrib", nfse.IBSCBS_cClassTrib, g)

    def _getRaiz(self):
        return etree.Element(self._tag("IBSCBS"))
