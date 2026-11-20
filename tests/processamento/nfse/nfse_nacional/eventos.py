import base64
import datetime
import hashlib
import unittest
from unittest import mock
import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from lxml import etree
from pynfe.entidades.certificado import CertificadoA1
from pynfe.processamento.nfse.compactador import Compactador
from pynfe.processamento.nfse.nfse_nacional import assinatura
from pynfe.processamento.nfse.nfse_nacional import eventos
from pynfe.processamento.nfse.nfse_nacional import servicos
from pynfe.processamento.nfse.nfse_nacional import validacao
from pynfe.processamento.nfse.nfse_nacional.flags import (
        NAMESPACE_NFSE, URL_HOMOLOGACAO, CANCELAMENTO_SERVICO_NAO_PRESTADO)
from pynfe.processamento.nfse.nfse_nacional.resposta import ErroSefin
from pynfe.processamento.nfse.nfse_nacional.serializacao import ErroRegraNegocio
from tests.processamento.nfse.nfse_nacional.assinatura import c14nTrecho
from tests.processamento.nfse.nfse_nacional.servicos import (
        resposta, cabecalho, CHAVE, REQUEST)

DS = "http://www.w3.org/2000/09/xmldsig#"
NS = {'n': NAMESPACE_NFSE, 'ds': DS}
CNPJ = "11222333000181"
JUSTIFICATIVA = "Serviço não foi prestado ao cliente"
EVENTO_XML = ('<evento xmlns="http://www.sped.fazenda.gov.br/nfse" versao="1.01">'
              '<infEvento Id="EVT%s101101001"/></evento>' % CHAVE)


class Serializacao(unittest.TestCase):

    def setUp(self) -> None:
        self.eventos = eventos.PedidoEvento()
        self.validacao = validacao.Validacao()

    def _gerar(self, **kwargs):
        dados = dict(chaveAcesso=CHAVE, autor=CNPJ, motivo=2,
                     descricao=JUSTIFICATIVA, homologacao=True,
                     dhEvento=datetime.datetime(2026, 11, 20, 15, 0, 0))
        dados.update(kwargs)
        return self.eventos.cancelamento(**dados)

    def _texto(self, pedido, caminho):
        return pedido.findtext(caminho, namespaces=NS)

    def test_cancelamento(self):
        p = self._gerar()
        info = p.find('n:infPedReg', NS)
        self.assertEqual(p.get('versao'), '1.01')
        self.assertEqual(info.get('Id'), 'PRE' + CHAVE + '101101')
        self.assertEqual(len(info.get('Id')), 59)
        self.assertEqual(self._texto(p, 'n:infPedReg/n:tpAmb'), '2')
        self.assertEqual(self._texto(p, 'n:infPedReg/n:dhEvento'), '2026-11-20T15:00:00-03:00')
        self.assertEqual(self._texto(p, 'n:infPedReg/n:CNPJAutor'), CNPJ)
        self.assertEqual(self._texto(p, 'n:infPedReg/n:chNFSe'), CHAVE)
        self.assertEqual(self._texto(p, 'n:infPedReg/n:e101101/n:xDesc'), 'Cancelamento de NFS-e')
        self.assertEqual(self._texto(p, 'n:infPedReg/n:e101101/n:cMotivo'), '2')
        self.assertEqual(self._texto(p, 'n:infPedReg/n:e101101/n:xMotivo'), JUSTIFICATIVA)
        self.assertTrue(self.validacao.validarPedidoEvento(p))

    def test_producao(self):
        self.assertEqual(self._texto(self._gerar(homologacao=False), 'n:infPedReg/n:tpAmb'), '1')

    def test_autor_cpf(self):
        p = self._gerar(autor="123.456.789-09")
        self.assertEqual(self._texto(p, 'n:infPedReg/n:CPFAutor'), '12345678909')
        self.assertTrue(self.validacao.validarPedidoEvento(p))

    def test_dhEvento_padrao(self):
        p = self._gerar(dhEvento=None)
        dh = datetime.datetime.strptime(self._texto(p, 'n:infPedReg/n:dhEvento')[:19],
                                        '%Y-%m-%dT%H:%M:%S')
        self.assertLess(dh, datetime.datetime.now())

    def test_motivo_invalido(self):
        with self.assertRaises(ErroRegraNegocio):
            self._gerar(motivo=3)

    def test_justificativa_curta(self):
        with self.assertRaises(ErroRegraNegocio):
            self._gerar(descricao="Erro")

    def test_justificativa_longa(self):
        with self.assertRaises(ErroRegraNegocio):
            self._gerar(descricao="x" * 256)

    def test_autor_invalido(self):
        with self.assertRaises(ErroRegraNegocio):
            self._gerar(autor="123")

    def test_chave_invalida(self):
        with self.assertRaises(ErroRegraNegocio):
            self._gerar(chaveAcesso="123")


class Assinatura(unittest.TestCase):

    def setUp(self) -> None:
        self.certificado = "./tests/certificado.pfx"
        self.senha = bytes("123456", encoding="utf-8")
        self.pedido = eventos.PedidoEvento().cancelamento(
            CHAVE, CNPJ, 1, "Erro na emissão da nota fiscal", homologacao=True)

    def test_assinatura(self):
        a = assinatura.Assinatura(self.certificado, self.senha).assinarPedidoEvento(self.pedido)
        idPedido = a.find('n:infPedReg', NS).get('Id')
        ref = a.find('ds:Signature/ds:SignedInfo/ds:Reference', NS)
        self.assertEqual(ref.get('URI'), '#' + idPedido)
        self.assertEqual([c.tag for c in a],
                         ['{%s}infPedReg' % NAMESPACE_NFSE, '{%s}Signature' % DS])
        self.assertTrue(validacao.Validacao().validarPedidoEvento(a))

        # Digest e assinatura conferidos com C14N independente do libxml2
        xml = etree.tostring(a, encoding="UTF-8")
        self.assertEqual(ref.findtext('ds:DigestValue', namespaces=NS),
                         base64.b64encode(hashlib.sha1(
                             c14nTrecho(xml, 'infPedReg', NAMESPACE_NFSE)).digest()).decode())
        _, cert = CertificadoA1(self.certificado).separar_arquivo(self.senha)
        chave = x509.load_pem_x509_certificate(cert.encode()).public_key()
        valor = base64.b64decode(a.findtext('ds:Signature/ds:SignatureValue', namespaces=NS))
        chave.verify(valor, c14nTrecho(xml, 'SignedInfo', DS), padding.PKCS1v15(), hashes.SHA1())

    def test_mantem_acentos(self):
        a = assinatura.Assinatura(self.certificado, self.senha).assinarPedidoEvento(self.pedido)
        self.assertEqual(a.findtext('n:infPedReg/n:e101101/n:xMotivo', namespaces=NS),
                         'Erro na emissão da nota fiscal')


class Cancelamento(unittest.TestCase):

    def setUp(self) -> None:
        self.servicos = servicos.Servicos("./tests/certificado.pfx", b"123456")
        self.compactador = Compactador()

    def _cancelar(self):
        return self.servicos.cancelar(CHAVE, CNPJ, CANCELAMENTO_SERVICO_NAO_PRESTADO,
                                      JUSTIFICATIVA, homologacao=True)

    def test_cancelar(self):
        with mock.patch(REQUEST, return_value=resposta(201, cabecalho(
                eventoXmlGZipB64=self.compactador.compactar(EVENTO_XML)))) as req:
            r = self._cancelar()
        metodo, url = req.call_args.args
        self.assertEqual((metodo, url), ("POST", URL_HOMOLOGACAO + "/nfse/" + CHAVE + "/eventos"))
        pedido = etree.fromstring(self.compactador.descompactar(
            req.call_args.kwargs["json"]["pedidoRegistroEventoXmlGZipB64"]).encode())
        self.assertEqual(pedido.findtext('n:infPedReg/n:e101101/n:cMotivo', namespaces=NS), '2')
        self.assertIsNotNone(pedido.find('ds:Signature', NS))
        self.assertTrue(validacao.Validacao().validarPedidoEvento(pedido))
        self.assertEqual(r["eventoXml"], EVENTO_XML)
        self.assertEqual(r["tipoAmbiente"], 2)

    def test_rejeicao(self):
        corpo = cabecalho(erro={"codigo": "E1800", "descricao": "NFS-e já cancelada",
                                "complemento": None})
        with mock.patch(REQUEST, return_value=resposta(400, corpo)):
            with self.assertRaises(ErroSefin) as cm:
                self._cancelar()
        self.assertEqual(cm.exception.status, 400)
        self.assertEqual(cm.exception.codigos, ["E1800"])

    def test_regra_nao_envia(self):
        with mock.patch(REQUEST) as req:
            with self.assertRaises(ErroRegraNegocio):
                self.servicos.cancelar(CHAVE, CNPJ, 1, "curta", homologacao=True)
        req.assert_not_called()

    def test_recuperado_apos_timeout(self):
        chamadas = []

        def req(metodo, url, json=None, **kw):
            chamadas.append((metodo, url))
            if metodo == "POST":
                raise requests.Timeout("tempo esgotado")
            return resposta(200, cabecalho(eventoXmlGZipB64=self.compactador.compactar(EVENTO_XML)))

        with mock.patch(REQUEST, side_effect=req):
            r = self._cancelar()
        self.assertEqual(chamadas[1], ("GET", URL_HOMOLOGACAO + "/nfse/" + CHAVE + "/eventos/101101/1"))
        self.assertTrue(r["recuperado"])
        self.assertEqual(r["eventoXml"], EVENTO_XML)

    def test_nao_registrado_apos_falha(self):
        def req(metodo, url, json=None, **kw):
            if metodo == "POST":
                raise requests.ConnectionError("conexão recusada")
            return resposta(404, cabecalho(erro={"codigo": "E404", "descricao": "Nenhum evento"}))

        with mock.patch(REQUEST, side_effect=req):
            with self.assertRaises(servicos.ErroComunicacao) as cm:
                self._cancelar()
        self.assertEqual(cm.exception.identificador, "PRE" + CHAVE + "101101")

    def test_erro_ssl(self):
        with mock.patch(REQUEST, side_effect=requests.exceptions.SSLError("certificate verify failed")) as req:
            with self.assertRaises(requests.exceptions.SSLError):
                self._cancelar()
        self.assertEqual(req.call_count, 1)

    def test_consultar_evento(self):
        with mock.patch(REQUEST, return_value=resposta(200, cabecalho(
                eventoXmlGZipB64=self.compactador.compactar(EVENTO_XML)))) as req:
            r = self.servicos.consultarEvento(CHAVE, homologacao=True)
        self.assertEqual(req.call_args.args,
                         ("GET", URL_HOMOLOGACAO + "/nfse/" + CHAVE + "/eventos/101101/1"))
        self.assertEqual(r["eventoXml"], EVENTO_XML)


if __name__ == '__main__':
    unittest.main()
