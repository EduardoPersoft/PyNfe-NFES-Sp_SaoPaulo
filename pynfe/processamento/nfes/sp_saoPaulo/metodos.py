from lxml import etree
from pynfe.processamento.nfes.sp_saoPaulo.flags import (
        NAMESPACE_NFES,
        VERSAO_SCHEMA
        )

class Metodos(object):

    def enviarLote(self, dados, homologacao=False):
        metodo = "EnvioLoteRPSRequest"
        if homologacao:
            metodo = 'TesteEnvioLoteRPSRequest'
        m = etree.Element("MensagemXML")
        m.append(dados)
        r = etree.Element(metodo, 
                          xmlns=NAMESPACE_NFES)
        etree.SubElement(r, "VersaoSchema").text = VERSAO_SCHEMA
        r.append(m)
        return r



