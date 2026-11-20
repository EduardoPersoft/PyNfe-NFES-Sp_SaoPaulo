import datetime
import unittest
from decimal import Decimal
from lxml import etree
from pynfe.entidades.cliente import Cliente
from pynfe.entidades.emitente import Emitente
from pynfe.entidades.notafiscal import NotaFiscalServico
from pynfe.entidades.servico import Servico
from pynfe.processamento.nfse.nfse_nacional import serializacao
from pynfe.processamento.nfse.nfse_nacional import validacao
from pynfe.processamento.nfse.nfse_nacional.flags import NAMESPACE_NFSE

NS = {'n': NAMESPACE_NFSE}


def get_nfse(**kwargs) -> NotaFiscalServico:
    emitente = Emitente(
        razao_social="Empresa Teste Ltda",
        cnpj="11222333000181",
        inscricao_municipal="12345678",
        endereco_logradouro="Rua Teste",
        endereco_numero="100",
        endereco_bairro="Centro",
        endereco_cep="01001-000",
        endereco_uf="SP",
        endereco_cod_municipio="3550308",
        endereco_telefone="(11) 3333-4444",
    )
    cliente = Cliente(
        razao_social="Cliente Teste",
        tipo_documento="CPF",
        numero_documento="123.456.789-09",
        email="cliente@example.com",
        endereco_logradouro="Avenida Cliente",
        endereco_numero="200",
        endereco_complemento="Sala 1",
        endereco_bairro="Bairro",
        endereco_cep="20040002",
        endereco_uf="RJ",
        endereco_cod_municipio="3304557",
    )
    servico = Servico(
        valor_servico=Decimal("1259.52"),
        iss_retido=2,
        discriminacao="Serviço de manutenção de sistemas",
        codigo_municipio="3550308",
        codigo_tributacao_nacional="010701",
        nbs="1.1501.30.00",
        aliquota=Decimal("2.00"),
        valor_inss=Decimal("0"),
        valor_ir=Decimal("0"),
        valor_csll=Decimal("0"),
    )
    dados = dict(
        identificador="1",
        serie="1",
        data_emissao=datetime.datetime(2026, 11, 20, 10, 30, 0),
        servico=servico,
        emitente=emitente,
        cliente=cliente,
        simples=1,
    )
    dados.update(kwargs)
    return NotaFiscalServico(**dados)


class Serializacao(unittest.TestCase):

    def setUp(self) -> None:
        self.serializacao = serializacao.Serializacao()
        self.validacao = validacao.Validacao()

    def _validar(self, dps):
        r = self.validacao.validarDPS(dps)
        for erro in self.validacao.erros:
            print(f"- Linha {erro.line}: {erro.message}")
        self.assertTrue(r)

    def _texto(self, dps, caminho):
        return dps.findtext(caminho, namespaces=NS)

    def test_validacao_xsd(self):
        self._validar(self.serializacao.gerar(get_nfse()))

    def test_id(self):
        dps = self.serializacao.gerar(get_nfse(identificador="123", serie="7"))
        infDPS = dps.find('n:infDPS', NS)
        self.assertEqual(infDPS.get('Id'),
                         'DPS' + '3550308' + '2' + '11222333000181'
                         + '00007' + '000000000000123')
        self.assertEqual(len(infDPS.get('Id')), 45)

    def test_id_prestador_cpf(self):
        nfse = get_nfse()
        nfse.emitente.cnpj = "12345678909"
        dps = self.serializacao.gerar(nfse)
        self.assertEqual(dps.find('n:infDPS', NS).get('Id')[10:25],
                         '1' + '00012345678909')
        self.assertEqual(self._texto(dps, 'n:infDPS/n:prest/n:CPF'), '12345678909')
        self._validar(dps)

    def test_ambiente(self):
        self.assertEqual(self._texto(self.serializacao.gerar(get_nfse()),
                                     'n:infDPS/n:tpAmb'), '1')
        dps = self.serializacao.gerar(get_nfse(), homologacao=True)
        self.assertEqual(self._texto(dps, 'n:infDPS/n:tpAmb'), '2')

    def test_dhEmi(self):
        dps = self.serializacao.gerar(get_nfse())
        self.assertEqual(self._texto(dps, 'n:infDPS/n:dhEmi'),
                         '2026-11-20T10:30:00-03:00')
        fuso = datetime.timezone(datetime.timedelta(hours=-4))
        nfse = get_nfse(data_emissao=datetime.datetime(2026, 11, 20, 10, 30,
                                                       tzinfo=fuso))
        dps = self.serializacao.gerar(nfse)
        self.assertEqual(self._texto(dps, 'n:infDPS/n:dhEmi'),
                         '2026-11-20T10:30:00-04:00')

    def test_prestador_simples(self):
        dps = self.serializacao.gerar(get_nfse())
        self.assertEqual(self._texto(dps, 'n:infDPS/n:prest/n:regTrib/n:opSimpNac'), '3')
        self.assertEqual(self._texto(dps, 'n:infDPS/n:prest/n:regTrib/n:regApTribSN'), '1')
        # Emitente prestador: nome e endereço vêm do cadastro nacional
        self.assertIsNone(dps.find('n:infDPS/n:prest/n:xNome', NS))
        self.assertIsNone(dps.find('n:infDPS/n:prest/n:end', NS))

    def test_prestador_nao_optante(self):
        dps = self.serializacao.gerar(get_nfse(simples=2))
        self.assertEqual(self._texto(dps, 'n:infDPS/n:prest/n:regTrib/n:opSimpNac'), '1')
        self.assertIsNone(dps.find('n:infDPS/n:prest/n:regTrib/n:regApTribSN', NS))
        self._validar(dps)

    def test_tomador(self):
        dps = self.serializacao.gerar(get_nfse())
        self.assertEqual(self._texto(dps, 'n:infDPS/n:toma/n:CPF'), '12345678909')
        self.assertEqual(self._texto(dps, 'n:infDPS/n:toma/n:end/n:endNac/n:CEP'), '20040002')

    def test_sem_tomador(self):
        self._validar(self.serializacao.gerar(get_nfse(cliente=None)))

    def test_iss_retido(self):
        nfse = get_nfse()
        nfse.servico.iss_retido = 1
        dps = self.serializacao.gerar(nfse)
        self.assertEqual(self._texto(dps, 'n:infDPS/n:valores/n:trib/n:tribMun/n:tpRetISSQN'), '2')

    def test_valores(self):
        nfse = get_nfse()
        nfse.servico.desconto_incondicionado = Decimal("10")
        nfse.servico.valor_ir = Decimal("15.5")
        dps = self.serializacao.gerar(nfse)
        self.assertEqual(self._texto(dps, 'n:infDPS/n:valores/n:vServPrest/n:vServ'), '1259.52')
        self.assertEqual(self._texto(dps, 'n:infDPS/n:valores/n:vDescCondIncond/n:vDescIncond'), '10.00')
        self.assertEqual(self._texto(dps, 'n:infDPS/n:valores/n:trib/n:tribFed/n:vRetIRRF'), '15.50')
        self._validar(dps)

    def test_ibscbs(self):
        nfse = get_nfse(IBSCBS_finNFSe=0, IBSCBS_indFinal=0,
                        IBSCBS_cIndOp="100301", IBSCBS_indDest=1,
                        IBSCBS_CST="000", IBSCBS_cClassTrib="000001")
        dps = self.serializacao.gerar(nfse)
        self.assertEqual(self._texto(dps, 'n:infDPS/n:IBSCBS/n:valores/n:trib/n:gIBSCBS/n:cClassTrib'), '000001')
        self._validar(dps)


if __name__ == '__main__':
    unittest.main()
