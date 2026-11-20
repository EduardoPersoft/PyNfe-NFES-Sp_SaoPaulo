"""Envia uma NFS-e de teste para a Sefin Nacional em HOMOLOGAÇÃO
(produção restrita) e mostra o resultado.

Não faz parte da suíte de testes: precisa de certificado ICP-Brasil real e
de acesso à internet. Sempre usa o ambiente de homologação.

Uso, a partir da raiz do projeto:

    cp tests/processamento/nfse/nfse_nacional/homologacao_exemplo.json \\
       tests/processamento/nfse/nfse_nacional/homologacao.json
    # preencha homologacao.json com os dados reais da empresa

    # 1) Gera, assina e valida a DPS sem enviar
    python -m tests.processamento.nfse.nfse_nacional.enviar_homologacao --gerar-apenas

    # 2) Envia (use um número de DPS ainda não usado)
    python -m tests.processamento.nfse.nfse_nacional.enviar_homologacao --numero 2

    # Consulta uma NFS-e já gerada
    python -m tests.processamento.nfse.nfse_nacional.enviar_homologacao --consultar CHAVE

    # Cancela uma NFS-e (autor: CNPJ do emitente em homologacao.json)
    python -m tests.processamento.nfse.nfse_nacional.enviar_homologacao \
        --cancelar CHAVE --motivo 1 --justificativa "Erro na emissão da nota de teste"

A senha do certificado é lida da variável de ambiente NFSE_SENHA ou pedida
no terminal; ela não é gravada em lugar nenhum. Os XMLs gerados são salvos
em homologacao_saida/ (ignorado pelo git).
"""
import argparse
import datetime
import decimal
import getpass
import json
import os
import sys

import requests
from lxml import etree

from pynfe.entidades.cliente import Cliente
from pynfe.entidades.emitente import Emitente
from pynfe.entidades.notafiscal import NotaFiscalServico
from pynfe.entidades.servico import Servico
from pynfe.processamento.nfse.nfse_nacional.flags import URL_HOMOLOGACAO, NAMESPACE_NFSE
from pynfe.processamento.nfse.nfse_nacional.resposta import ErroSefin
from pynfe.processamento.nfse.nfse_nacional.serializacao import ErroRegraNegocio
from pynfe.processamento.nfse.nfse_nacional.servicos import ErroComunicacao, Servicos

PASTA = os.path.dirname(os.path.abspath(__file__))
CONFIG_PADRAO = os.path.join(PASTA, "homologacao.json")
SAIDA_PADRAO = os.path.join(PASTA, "homologacao_saida")

DECIMAIS = {"valor_servico", "aliquota", "desconto_incondicionado",
            "desconto_condicionado", "valor_inss", "valor_ir", "valor_csll",
            "percentual_tributos_sn"}
TUPLAS = {"valor_tributos_aproximados", "percentual_tributos_aproximados"}


def _converter(dados):
    r = {}
    for k, v in dados.items():
        if v is None or k.startswith("_"):
            continue
        if k in DECIMAIS:
            v = decimal.Decimal(str(v))
        elif k in TUPLAS:
            v = tuple(decimal.Decimal(str(x)) for x in v)
        elif k == "data_competencia":
            v = datetime.date.fromisoformat(v)
        r[k] = v
    return r


def montar_nfse(config, numero=None, serie=None):
    nota = _converter(config["nota"])
    nota["identificador"] = str(numero or nota.pop("numero"))
    nota.pop("numero", None)
    if serie:
        nota["serie"] = str(serie)
    # Um minuto antes do horário local: a Sefin rejeita emissão posterior
    # ao processamento (E0008) e o relógio local pode estar adiantado.
    nota["data_emissao"] = datetime.datetime.now().replace(microsecond=0) \
        - datetime.timedelta(minutes=1)
    cliente = config.get("cliente")
    return NotaFiscalServico(
        emitente=Emitente(**_converter(config["emitente"])),
        cliente=Cliente(**_converter(cliente)) if cliente else None,
        servico=Servico(**_converter(config["servico"])),
        **nota)


def salvar(pasta, nome, conteudo):
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, nome)
    if isinstance(conteudo, etree._Element):
        conteudo = etree.tostring(conteudo, encoding="unicode", pretty_print=True)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)
    return caminho


def senha_certificado():
    senha = os.environ.get("NFSE_SENHA")
    if senha is None:
        senha = getpass.getpass("Senha do certificado: ")
    return senha.encode("utf-8")


def main():
    p = argparse.ArgumentParser(description="Teste da NFS-e Nacional em homologação.")
    p.add_argument("--config", default=CONFIG_PADRAO,
                   help="arquivo JSON com os dados (padrão: homologacao.json)")
    p.add_argument("--numero", help="número da DPS (substitui nota.numero)")
    p.add_argument("--serie", help="série da DPS (substitui nota.serie)")
    p.add_argument("--gerar-apenas", action="store_true",
                   help="gera, assina e valida a DPS, sem enviar")
    p.add_argument("--consultar", metavar="CHAVE",
                   help="consulta uma NFS-e pela chave de acesso")
    p.add_argument("--cancelar", metavar="CHAVE",
                   help="cancela uma NFS-e pela chave de acesso")
    p.add_argument("--motivo", type=int, default=1,
                   help="motivo do cancelamento: 1 - Erro na Emissão, "
                        "2 - Serviço não Prestado, 9 - Outros (padrão 1)")
    p.add_argument("--justificativa", default="Cancelamento de nota de teste em homologação",
                   help="justificativa do cancelamento, de 15 a 255 caracteres")
    p.add_argument("--cadeia", help="arquivo PEM com a cadeia de certificados "
                                    "do servidor, se houver erro de SSL")
    p.add_argument("--timeout", type=int, default=60)
    p.add_argument("--saida", default=SAIDA_PADRAO, help="pasta dos XMLs gerados")
    args = p.parse_args()

    if not os.path.exists(args.config):
        sys.exit("Arquivo %s não encontrado. Copie homologacao_exemplo.json para "
                 "homologacao.json e preencha." % args.config)
    with open(args.config, encoding="utf-8") as f:
        config = json.load(f)

    certificado = config["certificado"]
    if not os.path.exists(certificado):
        sys.exit("Certificado %s não encontrado." % certificado)

    servicos = Servicos(certificado, senha_certificado(), timeout=args.timeout,
                        verificar_ssl=args.cadeia or True)

    print("Ambiente: HOMOLOGAÇÃO (%s)" % URL_HOMOLOGACAO)

    try:
        if args.consultar:
            r = servicos.consultar(args.consultar, homologacao=True)
            print("NFS-e encontrada: %s" % r["chaveAcesso"])
            print("XML salvo em %s" % salvar(args.saida, "nfse_%s.xml" % r["chaveAcesso"], r["nfseXml"]))
            return 0

        if args.cancelar:
            pedido = servicos.gerarPedidoCancelamento(
                args.cancelar, config["emitente"]["cnpj"], args.motivo,
                args.justificativa, homologacao=True)
            idPedido = pedido.find("{%s}infPedReg" % NAMESPACE_NFSE).get("Id")
            print("Pedido de cancelamento gerado, assinado e válido no XSD: %s" % idPedido)
            print("XML salvo em %s" % salvar(args.saida, "%s.xml" % idPedido, pedido))
            if args.gerar_apenas:
                return 0
            print("Enviando...")
            r = servicos.cancelar(args.cancelar, config["emitente"]["cnpj"], args.motivo,
                                  args.justificativa, homologacao=True)
            print("\nNFS-e cancelada%s!" % (" (recuperado após falha de rede)"
                                            if r.get("recuperado") else ""))
            print("  Processado em: %s" % r.get("dataHoraProcessamento"))
            print("  Evento salvo em %s" % salvar(
                args.saida, "evento_cancelamento_%s.xml" % args.cancelar, r["eventoXml"]))
            return 0

        nfse = montar_nfse(config, args.numero, args.serie)
        dps = servicos.gerarDPS(nfse, homologacao=True)
        idDps = dps.find("{%s}infDPS" % NAMESPACE_NFSE).get("Id")
        print("DPS gerada, assinada e válida no XSD: %s" % idDps)
        print("XML salvo em %s" % salvar(args.saida, "%s.xml" % idDps, dps))
        if args.gerar_apenas:
            return 0

        print("Enviando...")
        r = servicos.enviar(nfse, homologacao=True)
    except ErroRegraNegocio as e:
        print("\nRegra de negócio violada (nada foi enviado):\n  %s" % e)
        return 1
    except ErroSefin as e:
        print("\nA Sefin recusou (HTTP %s):" % e.status)
        for erro in e.erros:
            print("  %s %s%s" % (erro["codigo"], erro["descricao"],
                                 " (%s)" % erro["complemento"] if erro.get("complemento") else ""))
        if not e.erros:
            print("  %s" % (e.texto or "").strip()[:1000])
        return 1
    except ErroComunicacao as e:
        print("\nFalha de comunicação e a Sefin não registrou o envio. É seguro "
              "reenviar (no caso da nota, com o mesmo número).\n  %s" % e.causa)
        return 1
    except requests.exceptions.SSLError as e:
        print("\nErro de SSL ao conectar na Sefin. Se for a cadeia de certificados "
              "do servidor, informe-a com --cadeia arquivo.pem.\n  %s" % e)
        return 1
    except Exception as e:
        print("\nErro: %s" % e)
        return 1

    print("\nNFS-e gerada%s!" % (" (recuperada após falha de rede)" if r.get("recuperada") else ""))
    print("  Chave de acesso: %s" % r["chaveAcesso"])
    print("  Id da DPS:       %s" % r["idDps"])
    print("  Processada em:   %s" % r.get("dataHoraProcessamento"))
    for a in r.get("alertas") or []:
        print("  Alerta %s: %s" % (a["codigo"], a["descricao"]))
    print("  XML salvo em %s" % salvar(args.saida, "nfse_%s.xml" % r["chaveAcesso"], r["nfseXml"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
