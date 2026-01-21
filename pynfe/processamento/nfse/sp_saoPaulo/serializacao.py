from lxml import etree
import decimal
from pynfe.processamento.nfse.sp_saoPaulo import tipos

NAMESPACE_NFES = "http://www.prefeitura.sp.gov.br/nfe"
XSD = "http://www.w3.org/2001/XMLSchema"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
VERSAO = "2"

class Serializacao(object):

    def gerar(self, nfse):
        solicitacao = "PedidoEnvioLoteRPS"
        self._nfse = nfse
        if not isinstance(nfse, list):
            self._nfse = [nfse]
        r = etree.Element(solicitacao, 
                          nsmap={"xsd": XSD, "xsi": XSI},
                          xmlns=NAMESPACE_NFES)
        r.append(Cabecalho(self._nfse).element)
        for n in self._nfse:
            r.append(RPS(n).element)
        #print(etree.tostring(r, encoding="unicode", pretty_print=False))
        return r

class Elemento(object):

    def __init__(self, nfse):
        self._nfse = nfse
        self._element = self._getRaiz()

    @property
    def element(self):
        return self._element

    def _getRaiz(self) -> etree.Element:
        pass

    def _add(self, element, value, raiz=None):
        if raiz is None:
            raiz=self._element
        if isinstance(value, int):
            value = str(value)
        if isinstance(value, decimal.Decimal):
            value ='%.2f' % value
        etree.SubElement(raiz, element).text = value

class Cabecalho(Elemento):

    def __init__(self, nfse):
        super().__init__(nfse)
        self._element.append(self._remetente)
        self._element.append(self._transacao)
        self._element.append(self._dtInicio)
        self._element.append(self._dtFim)
        self._element.append(self._qtdRPS)

    def _getRaiz(self):
        r = etree.Element("Cabecalho")
        r.attrib["Versao"] = VERSAO
        r.attrib["xmlns"] = ""
        return r


    @property
    def _remetente(self):
        r = etree.Element("CPFCNPJRemetente")
        cnpj = etree.Element("CNPJ")
        cnpj.text = self._nfse[0].emitente.cnpj
        r.append(cnpj)
        return r

    @property
    def _transacao(self):
        r = etree.Element("transacao")
        r.text = "true"
        return r

    @property
    def _dtInicio(self):
        menor = self._nfse[0].data_emissao
        for n in self._nfse:
            if n.data_emissao<menor:
                menor=n.data_emissao
        r = etree.Element('dtInicio')
        r.text = menor.strftime("%Y-%m-%d") 
        return r

    @property
    def _dtFim(self):
        maior = self._nfse[0].data_emissao
        for n in self._nfse:
            if n.data_emissao<maior:
                maior=n.data_emissao
        r = etree.Element('dtFim')
        r.text = maior.strftime("%Y-%m-%d") 
        return r

    @property
    def _qtdRPS(self):
        r = etree.Element('QtdRPS')
        r.text = str(len(self._nfse))
        return r

class RPS(Elemento):

    def __init__(self, nfse):
        super().__init__(nfse)
        self._tipos = tipos.Tipos(nfse)
        self._add("Assinatura", self._nfse.assinatura)
        self._element.append(self._chaveRPS)
        self._add("TipoRPS", self._tipos.tipoRPS)
        self._add("DataEmissao", self._nfse.data_emissao.strftime("%Y-%m-%d"))
        self._add("StatusRPS", 'N')
        self._add("TributacaoRPS", self._tipos.tributacaoRPS)
        self._add("ValorDeducoes", self._nfse.servico.valor_deducoes)
        self._add("ValorPIS", nfse.servico.valor_pis)
        self._add("ValorCOFINS", self._nfse.servico.valor_confins)
        self._add("ValorINSS", self._nfse.servico.valor_inss)
        self._add("ValorIR", self._nfse.servico.valor_ir)
        self._add("ValorCSLL", self._nfse.servico.valor_csll)
        self._add("CodigoServico", self._nfse.servico.codigo_tributacao_municipio)
        self._add("AliquotaServicos", self._nfse.servico.aliquota)
        self._add("ISSRetido", self._tipos.issRetido)
        self._element.append(self._cnpjCpfTomador)
        self._add("RazaoSocialTomador", self._nfse.cliente.razao_social)
        self._element.append(self._enderecoTomador)
        self._add("Discriminacao", self._nfse.servico.discriminacao)
        self._add("ValorFinalCobrado", self._nfse.servico.valor_liquido)
        self._add("ValorIPI", self._nfse.servico.valor_ipi)
        self._add("ExigibilidadeSuspensa", self._nfse.servico.exigibilidade)
        self._add("PagamentoParceladoAntecipado", self._nfse.pgtoParcAntec)
        self._add("NBS", self._nfse.servico.nbs.replace('.',''))
        self._add("cLocPrestacao", self._nfse.cliente.endereco_cod_municipio)
        self._element.append(self._ibscbs)

    @property
    def _cnpjCpfTomador(self):
        r = etree.Element('CPFCNPJTomador')
        cnpjCpf = 'CNPJ'
        if self._nfse.cliente.tipo_documento=='CPF':
            cnpjCpf = 'CPF'
        self._add(cnpjCpf, self._nfse.cliente.numero_documento, raiz=r)
        return r

    @property
    def _enderecoTomador(self):
        r = etree.Element('EnderecoTomador')
        if hasattr(self._nfse.cliente, 'endereco_tipo_logradouro'):
            self._add("TipoLogradouro",
                      self._nfse.cliente.endereco_tipo_logradouro,
                      raiz=r)
        self._add("Logradouro", self._nfse.cliente.endereco_logradouro,
                  raiz=r)
        self._add("NumeroEndereco", self._nfse.cliente.endereco_numero,
                  raiz=r)
        self._add("ComplementoEndereco",
                  self._nfse.cliente.endereco_complemento,
                  raiz=r)
        self._add("Bairro", self._nfse.cliente.endereco_bairro, raiz=r)
        self._add("Cidade", self._nfse.cliente.endereco_cod_municipio, raiz=r)
        self._add("UF", self._nfse.cliente.endereco_uf, raiz=r)
        self._add("CEP", self._nfse.cliente.endereco_cep, raiz=r)
        return r

    @property
    def _chaveRPS(self):
        r = etree.Element("ChaveRPS")
        etree.SubElement(r, "InscricaoPrestador").text = self._nfse.emitente.inscricao_municipal
        etree.SubElement(r, "SerieRPS").text = self._nfse.serie
        etree.SubElement(r, "NumeroRPS").text = self._nfse.identificador
        return r

    def _getRaiz(self):
        return etree.Element("RPS", xmlns="") 

    @property
    def _ibscbs(self):
        r = etree.Element("IBSCBS")
        self._add("finNFSe", self._nfse.IBSCBS_finNFSe, raiz=r)
        self._add("indFinal", self._nfse.IBSCBS_indFinal, raiz=r)
        self._add("cIndOp", self._nfse.IBSCBS_cIndOp, raiz=r)
        if self._nfse.IBSCBS_tpOper:
            self._add("tpOper", self._nfse.IBSCBS_tpOper, raiz=r)
        self._add("indDest", self._nfse.IBSCBS_indDest, raiz=r)
        r.append(self._valores)
        return r

    @property
    def _valores(self):
        r = etree.Element("valores")
        t = etree.Element("trib")
        g = etree.Element('gIBSCBS')
        self._add("cClassTrib", self._nfse.IBSCBS_cClassTrib, raiz=g)
        t.append(g)
        r.append(t)
        return r

