from xml.sax.handler import property_dom_node
from lxml import etree
from pynfe.processamento.nfse.sp_saoPaulo.flags import (
        NAMESPACE_NFES,
        VERSAO_SCHEMA,
        VERSAO_SCHEMA_SIMPLES
        )

class Metodos(object):

    def __init__(self):
        self._schema='2'

    def enviarLote(self, dados, homologacao=False):
        metodo = "EnvioLoteRPSRequest"
        if homologacao:
            metodo = 'TesteEnvioLoteRPSRequest'
        m = etree.Element("MensagemXML")
        m.text = etree.CDATA(etree.tostring(dados, encoding="unicode", pretty_print=False))
        r = etree.Element(metodo, 
                          xmlns=NAMESPACE_NFES)
        etree.SubElement(r, "VersaoSchema").text = self._versaoSchema
        r.append(m)
        return r

    def setSchema(self, value):
        self._schema = value

    @property
    def schema(self):
        return self._schema

    @property 
    def _versaoSchema(self):
        if self._schema=='1':
            return VERSAO_SCHEMA_SIMPLES
        return VERSAO_SCHEMA


