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
        SIMPLES_MEI,
        SIMPLES_ME_EPP,
        TIPO_INSCRICAO_CPF,
        TIPO_INSCRICAO_CNPJ,
        SERIE_APLICATIVO_PROPRIO_MIN,
        SERIE_APLICATIVO_PROPRIO_MAX,
        )


class ErroRegraNegocio(Exception):
    """A DPS violaria uma regra de negócio da NFS-e Nacional e seria
    rejeitada pela Sefin. A mensagem começa com o código da regra."""


class Serializacao(object):
    """Gera o XML da DPS (Declaração de Prestação de Serviços) no leiaute
    1.01 da NFS-e Nacional a partir de um NotaFiscalServico.

    O XML é gerado sem assinatura. Levanta ErroRegraNegocio quando os dados
    violam uma regra de negócio que pode ser verificada localmente."""

    def gerar(self, nfse, homologacao=False):
        return DPS(nfse, homologacao).element


def _somenteNumeros(value):
    return re.sub(r'\D', '', str(value or ''))


# Valores derivados da nota, usados por mais de um grupo da DPS.

def _tpEmit(nfse):
    return int(getattr(nfse, 'tipo_emitente', None) or EMITENTE_PRESTADOR)


def _opSimpNac(nfse):
    op = getattr(nfse, 'op_simples_nacional', None)
    if op:
        return int(op)
    if nfse.simples == 1:
        return SIMPLES_ME_EPP
    return SIMPLES_NAO_OPTANTE


def _regApTribSN(nfse):
    """Só existe para ME/EPP (E0162/E0166). Padrão 1: tributos federais e
    municipal apurados pelo Simples Nacional."""
    if _opSimpNac(nfse) != SIMPLES_ME_EPP:
        return None
    return int(getattr(nfse, 'regime_apuracao_sn', None) or 1)


def _regEspTrib(nfse):
    return int(getattr(nfse, 'regime_especial', None) or 0)


def _tribISSQN(nfse):
    return int(getattr(nfse.servico, 'tributacao_issqn', None) or 1)


def _tpRetISSQN(nfse):
    """1 - Não retido; 2 - Retido pelo tomador; 3 - Retido pelo
    intermediário. iss_retido segue o padrão 1-Sim; 2-Não."""
    tp = getattr(nfse.servico, 'tipo_retencao_issqn', None)
    if tp:
        return int(tp)
    if nfse.servico.iss_retido == 1:
        return 2
    return 1


def _emitenteCPF(nfse):
    return len(_somenteNumeros(nfse.emitente.cnpj)) == 11


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
        self._validarSerie(nfse)
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
            if _vazio(_somenteNumeros(getattr(nfse.servico, 'nbs', None))):
                raise ErroRegraNegocio(
                    "E0322: é obrigatório informar o NBS (servico.nbs) "
                    "quando o grupo IBS/CBS é informado.")
            self._element.append(IBSCBS(nfse).element)

    @staticmethod
    def _validarSerie(nfse):
        serie = str(nfse.serie).strip()
        if not serie.isdigit() or not (
                SERIE_APLICATIVO_PROPRIO_MIN <= int(serie) <= SERIE_APLICATIVO_PROPRIO_MAX):
            raise ErroRegraNegocio(
                "E0010: a série da DPS emitida por aplicativo próprio deve "
                "estar entre 00001 e 49999 (informada: %r)." % nfse.serie)

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
        emissao = self._nfse.data_emissao
        if isinstance(d, datetime.datetime):
            d = d.date()
        if isinstance(emissao, datetime.datetime):
            emissao = emissao.date()
        if d > emissao:
            raise ErroRegraNegocio(
                "E0015: a data de competência não pode ser posterior à data "
                "de emissão da DPS.")
        return d.strftime('%Y-%m-%d')

    @property
    def _tpEmit(self):
        tp = _tpEmit(self._nfse)
        if tp != EMITENTE_PRESTADOR:
            raise ErroRegraNegocio(
                "E9996: nesta versão da Sefin Nacional só o prestador pode "
                "emitir a DPS (tipo_emitente = 1).")
        return tp

    @property
    def _cLocEmi(self):
        return _somenteNumeros(self._nfse.emitente.endereco_cod_municipio)


class Prestador(Elemento):

    def __init__(self, nfse):
        super().__init__(nfse)
        emitente = nfse.emitente
        self._documento(None, emitente.cnpj, self._element)
        # E0116/E0120: a IM deve ser informada se, e somente se, houver
        # registro do prestador no CNC do município emissor.
        if getattr(nfse, 'prestador_informar_im', True):
            self._addOpcional("IM", emitente.inscricao_municipal)
        # E0121/E0128: quando o emitente da DPS é o próprio prestador, nome
        # e endereço vêm do cadastro nacional e não podem ser informados.
        if _tpEmit(nfse) != EMITENTE_PRESTADOR:
            self._add("xNome", emitente.razao_social)
            self._element.append(Endereco(emitente).element)
        self._addOpcional("fone", _somenteNumeros(emitente.endereco_telefone))
        self._addOpcional("email", getattr(emitente, 'email', None))
        self._element.append(self._regTrib)

    def _getRaiz(self):
        return etree.Element(self._tag("prest"))

    @property
    def _regTrib(self):
        nfse = self._nfse
        r = etree.Element(self._tag("regTrib"))
        op = _opSimpNac(nfse)
        regAp = _regApTribSN(nfse)
        regEsp = _regEspTrib(nfse)
        if regEsp != 0:
            if op == SIMPLES_MEI:
                raise ErroRegraNegocio(
                    "E0174: o regime especial de tributação deve ser 0 "
                    "(nenhum) para MEI.")
            if op == SIMPLES_ME_EPP and regAp == 1:
                raise ErroRegraNegocio(
                    "E0175: o regime especial de tributação deve ser 0 "
                    "(nenhum) para ME/EPP com apuração pelo Simples Nacional "
                    "(regApTribSN = 1).")
            if _tribISSQN(nfse) != 1:
                raise ErroRegraNegocio(
                    "E0172: o regime especial de tributação deve ser 0 "
                    "(nenhum) quando a operação não é tributável.")
        self._add("opSimpNac", op, r)
        if regAp is not None:
            self._add("regApTribSN", regAp, r)
        self._add("regEspTrib", regEsp, r)
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
        elif cliente.tipo_documento != 'CPF':
            raise ErroRegraNegocio(
                "E0235: o endereço do tomador é obrigatório quando ele é "
                "identificado pelo CNPJ.")
        elif _tpRetISSQN(nfse) == 2:
            raise ErroRegraNegocio(
                "E0237: o endereço do tomador é obrigatório quando o ISSQN "
                "é retido pelo tomador.")
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
        nfse = self._nfse
        t = etree.Element(self._tag("trib"))
        m = self._sub("tribMun", t)
        self._add("tribISSQN", _tribISSQN(nfse), m)
        self._add("tpRetISSQN", self._tpRetISSQN, m)
        if self._informarAliquota:
            aliquota = getattr(nfse.servico, 'aliquota', None)
            if _vazio(aliquota):
                raise ErroRegraNegocio(
                    "E0619/E0621/E0628/E0640: a alíquota do ISSQN "
                    "(servico.aliquota) é obrigatória neste cenário.")
            if aliquota > 5:
                raise ErroRegraNegocio(
                    "E0595: a alíquota do ISSQN não pode ser superior a 5%.")
            self._add("pAliq", aliquota, m)
        self._tribFed(t)
        self._totTrib(t)
        return t

    @property
    def _tpRetISSQN(self):
        nfse = self._nfse
        tp = _tpRetISSQN(nfse)
        if tp != 1:
            if _tribISSQN(nfse) != 1:
                raise ErroRegraNegocio(
                    "E0580: não pode haver retenção do ISSQN quando a "
                    "operação não é tributável.")
            if _opSimpNac(nfse) == SIMPLES_MEI:
                raise ErroRegraNegocio(
                    "E0583: não pode haver retenção do ISSQN para MEI.")
            if _regEspTrib(nfse) != 0:
                raise ErroRegraNegocio(
                    "E0588: não pode haver retenção do ISSQN quando há regime "
                    "especial de tributação.")
            if tp == 2 and getattr(nfse, 'cliente', None) is None:
                raise ErroRegraNegocio(
                    "E0204: o tomador deve ser identificado quando o ISSQN é "
                    "retido pelo tomador.")
        return tp

    @property
    def _informarAliquota(self):
        """Decide se pAliq deve ser informado (regras E0595 a E0640).

        Quando o município de incidência tem convênio ativo no Sistema
        Nacional, a alíquota vem da parametrização do município e só deve
        ser informada por ME/EPP com apuração pelo SN e retenção do ISSQN.
        Quando o convênio não está ativo, a alíquota é obrigatória, exceto
        para ME/EPP com apuração pelo SN sem retenção.

        O atributo municipio_incidencia_conveniado (padrão True) indica se o
        convênio do município de incidência está ativo."""
        nfse = self._nfse
        op = _opSimpNac(nfse)
        if op == SIMPLES_MEI or _regEspTrib(nfse) != 0 or _tribISSQN(nfse) != 1:
            return False
        if op == SIMPLES_ME_EPP and _regApTribSN(nfse) == 1:
            return _tpRetISSQN(nfse) in (2, 3)
        return not getattr(nfse, 'municipio_incidencia_conveniado', True)

    def _tribFed(self, raiz):
        nfse = self._nfse
        servico = nfse.servico
        retencoes = [("vRetCP", getattr(servico, 'valor_inss', None)),
                     ("vRetIRRF", getattr(servico, 'valor_ir', None)),
                     ("vRetCSLL", getattr(servico, 'valor_csll', None))]
        if all(_vazio(v) for _, v in retencoes):
            return
        if _emitenteCPF(nfse):
            raise ErroRegraNegocio(
                "E0675: tributos federais não podem ser informados quando o "
                "emitente é pessoa física (CPF).")
        if _opSimpNac(nfse) == SIMPLES_MEI:
            raise ErroRegraNegocio(
                "E0676: tributos federais não podem ser informados quando o "
                "emitente é MEI.")
        valor = decimal.Decimal(servico.valor_servico)
        for nome, v in retencoes:
            if not _vazio(v) and not (0 < v < valor):
                raise ErroRegraNegocio(
                    "E0699/E0700/E0701: %s deve ser maior que zero e menor que "
                    "o valor do serviço." % nome)
        f = self._sub("tribFed", raiz)
        for nome, v in retencoes:
            self._addOpcional(nome, v, f)

    def _totTrib(self, raiz):
        """Total aproximado dos tributos (Lei 12.741/2012), regras
        E0710/E0712/E0713:

        - ME/EPP: pTotTribSN, vTotTrib ou pTotTrib (indTotTrib não é aceito);
        - Não optante: vTotTrib ou pTotTrib;
        - MEI: vTotTrib, pTotTrib ou indTotTrib = 0 (pTotTribSN não é aceito).

        Atributos da nota: percentual_tributos_sn, valor_tributos_aproximados
        e percentual_tributos_aproximados (estes dois são tuplas
        (federal, estadual, municipal)).
        """
        nfse = self._nfse
        op = _opSimpNac(nfse)
        pSN = getattr(nfse, 'percentual_tributos_sn', None)
        valores = getattr(nfse, 'valor_tributos_aproximados', None)
        percentuais = getattr(nfse, 'percentual_tributos_aproximados', None)
        tot = self._sub("totTrib", raiz)
        if valores:
            v = self._sub("vTotTrib", tot)
            for nome, valor in zip(("vTotTribFed", "vTotTribEst", "vTotTribMun"), valores):
                self._add(nome, decimal.Decimal(valor), v)
        elif percentuais:
            p = self._sub("pTotTrib", tot)
            for nome, valor in zip(("pTotTribFed", "pTotTribEst", "pTotTribMun"), percentuais):
                self._add(nome, decimal.Decimal(valor), p)
        elif not _vazio(pSN) and op == SIMPLES_ME_EPP:
            self._add("pTotTribSN", decimal.Decimal(pSN), tot)
        elif op == SIMPLES_MEI:
            self._add("indTotTrib", 0, tot)
        elif op == SIMPLES_ME_EPP:
            raise ErroRegraNegocio(
                "E0712: para ME/EPP informe percentual_tributos_sn, "
                "valor_tributos_aproximados ou percentual_tributos_aproximados.")
        else:
            raise ErroRegraNegocio(
                "E0713: para não optante do Simples Nacional informe "
                "valor_tributos_aproximados ou percentual_tributos_aproximados.")


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
