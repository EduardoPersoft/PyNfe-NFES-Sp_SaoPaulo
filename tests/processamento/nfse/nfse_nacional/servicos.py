import json
import os
import unittest
from unittest import mock
import requests
from lxml import etree
from pynfe.processamento.nfse import autorizador
from pynfe.processamento.nfse.compactador import Compactador
from pynfe.processamento.nfse.nfse_nacional import comunicacao
from pynfe.processamento.nfse.nfse_nacional import servicos
from pynfe.processamento.nfse.nfse_nacional.flags import (
        NAMESPACE_NFSE, URL_HOMOLOGACAO, URL_PRODUCAO)
from pynfe.processamento.nfse.nfse_nacional.resposta import ErroSefin
from tests.processamento.nfse.nfse_nacional.serializacao import get_nfse

NS = {'n': NAMESPACE_NFSE}
CHAVE = "3550308" + "2" * 43
REQUEST = 'pynfe.processamento.nfse.nfse_nacional.comunicacao.requests.request'
NFSE_XML = '<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse"><infNFSe Id="NFS1"/></NFSe>'


def resposta(status, corpo):
    r = mock.Mock()
    r.status_code = status
    if isinstance(corpo, dict):
        r.json.return_value = corpo
        r.text = json.dumps(corpo)
    else:
        r.json.side_effect = ValueError("não é JSON")
        r.text = corpo
    return r


def cabecalho(**kwargs):
    d = {"tipoAmbiente": 2, "versaoAplicativo": "SefinNac_1.0",
         "dataHoraProcessamento": "2026-11-20T10:30:05-03:00"}
    d.update(kwargs)
    return d


class Base(unittest.TestCase):

    def setUp(self) -> None:
        self.certificado = "./tests/certificado.pfx"
        self.senha = bytes("123456", encoding="utf-8")
        self.servicos = servicos.Servicos(self.certificado, self.senha)
        self.compactador = Compactador()

    def sucesso(self, idDps):
        return resposta(201, cabecalho(
            idDps=idDps, chaveAcesso=CHAVE,
            nfseXmlGZipB64=self.compactador.compactar(NFSE_XML),
            alertas=[{"codigo": "A001", "descricao": "Alerta", "complemento": None}]))


class Envio(Base):

    def test_envio_homologacao(self):
        with mock.patch(REQUEST) as req:
            req.side_effect = lambda m, url, json=None, **kw: self.sucesso(
                etree.fromstring(self.compactador.descompactar(json["dpsXmlGZipB64"]).encode())
                .find('n:infDPS', NS).get('Id'))
            r = self.servicos.enviar(get_nfse(), homologacao=True)

        metodo, url = req.call_args.args
        kw = req.call_args.kwargs
        self.assertEqual((metodo, url), ("POST", URL_HOMOLOGACAO + "/nfse"))
        self.assertEqual(kw["timeout"], 60)
        self.assertTrue(kw["verify"])
        # Certificado e chave em arquivos temporários, excluídos após o envio
        for arquivo in kw["cert"]:
            self.assertFalse(os.path.exists(arquivo))

        dps = etree.fromstring(
            self.compactador.descompactar(kw["json"]["dpsXmlGZipB64"]).encode())
        self.assertEqual(dps.findtext('n:infDPS/n:tpAmb', namespaces=NS), '2')
        self.assertIsNotNone(dps.find('{http://www.w3.org/2000/09/xmldsig#}Signature'))

        self.assertEqual(r["chaveAcesso"], CHAVE)
        self.assertEqual(r["idDps"], dps.find('n:infDPS', NS).get('Id'))
        self.assertEqual(r["nfseXml"], NFSE_XML)
        self.assertEqual(r["alertas"][0]["codigo"], "A001")

    def test_envio_producao(self):
        with mock.patch(REQUEST) as req:
            req.return_value = self.sucesso("DPS" + "1" * 42)
            self.servicos.enviar(get_nfse())
        self.assertEqual(req.call_args.args[1], URL_PRODUCAO + "/nfse")
        dps = etree.fromstring(self.compactador.descompactar(
            req.call_args.kwargs["json"]["dpsXmlGZipB64"]).encode())
        self.assertEqual(dps.findtext('n:infDPS/n:tpAmb', namespaces=NS), '1')

    def test_rejeicao(self):
        corpo = cabecalho(idDPS="DPS" + "1" * 42, erros=[
            {"codigo": "E0712", "descricao": "Para ME/EPP indTotTrib nunca poderá ser informado.",
             "complemento": None},
            {"codigo": "E0625", "descricao": "Não é permitido informar alíquota", "complemento": "x"}])
        with mock.patch(REQUEST, return_value=resposta(400, corpo)):
            with self.assertRaises(ErroSefin) as cm:
                self.servicos.enviar(get_nfse(), homologacao=True)
        e = cm.exception
        self.assertEqual(e.status, 400)
        self.assertEqual(e.codigos, ["E0712", "E0625"])
        self.assertEqual(e.idDps, "DPS" + "1" * 42)
        self.assertIn("E0712", str(e))

    def test_rejeicao_chaves_maiusculas(self):
        corpo = cabecalho(idDPS="DPS" + "1" * 42, erros=[
            {"Codigo": "E0014", "Descricao": "DPS já utilizada", "Complemento": "x"}])
        with mock.patch(REQUEST, return_value=resposta(400, corpo)):
            with self.assertRaises(ErroSefin) as cm:
                self.servicos.enviar(get_nfse(), homologacao=True)
        self.assertEqual(cm.exception.codigos, ["E0014"])
        self.assertIn("E0014 DPS já utilizada (x)", str(cm.exception))

    def test_rejeicao_formato_desconhecido(self):
        corpo = cabecalho(erros=[{"mensagem": "algo inesperado"}])
        with mock.patch(REQUEST, return_value=resposta(400, corpo)):
            with self.assertRaises(ErroSefin) as cm:
                self.servicos.enviar(get_nfse(), homologacao=True)
        self.assertIn("algo inesperado", str(cm.exception))

    def test_certificado_recusado(self):
        corpo = cabecalho(erros=[{"codigo": "E1200", "descricao": "Certificado de Transmissão Inválido"}])
        with mock.patch(REQUEST, return_value=resposta(403, corpo)):
            with self.assertRaises(ErroSefin) as cm:
                self.servicos.enviar(get_nfse(), homologacao=True)
        self.assertEqual(cm.exception.codigos, ["E1200"])

    def test_resposta_nao_json(self):
        with mock.patch(REQUEST, return_value=resposta(502, "<html>Bad Gateway</html>")):
            with self.assertRaises(ErroSefin) as cm:
                self.servicos.enviar(get_nfse(), homologacao=True)
        self.assertEqual(cm.exception.status, 502)
        self.assertIn("Bad Gateway", str(cm.exception))

    def test_regra_negocio_nao_envia(self):
        with mock.patch(REQUEST) as req:
            with self.assertRaises(servicos.serializacao.ErroRegraNegocio):
                self.servicos.enviar(get_nfse(serie="A1"))
        req.assert_not_called()


class Recuperacao(Base):
    """Falha de rede no envio: consulta a DPS antes de devolver o erro."""

    def test_nfse_gerada_apesar_do_timeout(self):
        chamadas = []

        def req(metodo, url, json=None, **kw):
            chamadas.append((metodo, url))
            if metodo == "POST":
                raise requests.Timeout("tempo esgotado")
            if "/dps/" in url:
                return resposta(200, cabecalho(idDps=url.rsplit("/", 1)[1], chaveAcesso=CHAVE))
            return resposta(200, cabecalho(chaveAcesso=CHAVE,
                                           nfseXmlGZipB64=self.compactador.compactar(NFSE_XML)))

        with mock.patch(REQUEST, side_effect=req):
            r = self.servicos.enviar(get_nfse(), homologacao=True)
        self.assertEqual([m for m, _ in chamadas], ["POST", "GET", "GET"])
        self.assertTrue(chamadas[1][1].startswith(URL_HOMOLOGACAO + "/dps/DPS"))
        self.assertEqual(chamadas[2][1], URL_HOMOLOGACAO + "/nfse/" + CHAVE)
        self.assertEqual(r["chaveAcesso"], CHAVE)
        self.assertTrue(r["recuperada"])
        self.assertTrue(r["idDps"].startswith("DPS"))

    def test_nfse_nao_gerada(self):
        def req(metodo, url, json=None, **kw):
            if metodo == "POST":
                raise requests.ConnectionError("conexão recusada")
            return resposta(404, cabecalho(erro={"codigo": "E404", "descricao": "Não encontrada"}))

        with mock.patch(REQUEST, side_effect=req):
            with self.assertRaises(servicos.ErroComunicacao) as cm:
                self.servicos.enviar(get_nfse(), homologacao=True)
        self.assertTrue(cm.exception.idDps.startswith("DPS"))
        self.assertIsInstance(cm.exception.causa, requests.ConnectionError)

    def test_erro_ssl_nao_e_falha_de_rede(self):
        with mock.patch(REQUEST, side_effect=requests.exceptions.SSLError("certificate verify failed")) as req:
            with self.assertRaises(requests.exceptions.SSLError):
                self.servicos.enviar(get_nfse(), homologacao=True)
        self.assertEqual(req.call_count, 1)

    def test_consulta_tambem_falha(self):
        with mock.patch(REQUEST, side_effect=requests.Timeout("tempo esgotado")):
            with self.assertRaises(servicos.ErroComunicacao):
                self.servicos.enviar(get_nfse(), homologacao=True)


class Consultas(Base):

    def test_consultar(self):
        with mock.patch(REQUEST, return_value=resposta(200, cabecalho(
                chaveAcesso=CHAVE, nfseXmlGZipB64=self.compactador.compactar(NFSE_XML)))) as req:
            r = self.servicos.consultar(CHAVE, homologacao=True)
        self.assertEqual(req.call_args.args, ("GET", URL_HOMOLOGACAO + "/nfse/" + CHAVE))
        self.assertEqual(r["nfseXml"], NFSE_XML)

    def test_consultar_chave_invalida(self):
        with mock.patch(REQUEST) as req:
            with self.assertRaises(ValueError):
                self.servicos.consultar("123")
        req.assert_not_called()

    def test_consultar_dps_inexistente(self):
        corpo = cabecalho(erro={"codigo": "E2000", "descricao": "DPS não encontrada", "complemento": None})
        with mock.patch(REQUEST, return_value=resposta(404, corpo)):
            with self.assertRaises(ErroSefin) as cm:
                self.servicos.consultarDps("DPS" + "1" * 42)
        self.assertEqual(cm.exception.status, 404)
        self.assertEqual(cm.exception.codigos, ["E2000"])

    def test_registrar_evento(self):
        com = comunicacao.Comunicacao(self.certificado, self.senha, homologacao=True)
        with mock.patch(REQUEST, return_value=resposta(201, cabecalho())) as req:
            com.registrarEvento(CHAVE, "abc")
        self.assertEqual(req.call_args.args, ("POST", URL_HOMOLOGACAO + "/nfse/" + CHAVE + "/eventos"))
        self.assertEqual(req.call_args.kwargs["json"], {"pedidoRegistroEventoXmlGZipB64": "abc"})


class Autorizador(unittest.TestCase):

    def test_nfse_nacional(self):
        s = autorizador.get('3550308', "./tests/certificado.pfx", b"123456", nfse_nacional=True)
        self.assertIsInstance(s, servicos.Servicos)
        self.assertEqual(s._timeout, 60)

    def test_nfse_nacional_timeout(self):
        s = autorizador.get('3550308', "./tests/certificado.pfx", b"123456",
                            nfse_nacional=True, timeout=15)
        self.assertEqual(s._timeout, 15)

    def test_sao_paulo(self):
        from pynfe.processamento.nfse.sp_saoPaulo import servicos as sp
        s = autorizador.get('3550308', "./tests/certificado.pfx", b"123456")
        self.assertIsInstance(s, sp.Servicos)


if __name__ == '__main__':
    unittest.main()
