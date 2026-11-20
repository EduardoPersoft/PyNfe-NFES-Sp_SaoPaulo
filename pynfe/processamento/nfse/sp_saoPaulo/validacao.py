import os
from lxml import etree
from pynfe.utils import CAMINHO_DATA

class Validacao(object):

    def __init__(self):
        self._schema = '2'
        self._folder = os.path.join(CAMINHO_DATA, 'XSDs', 'NFS-e', 'sp_saoPaulo')
        
    def validarLote(self, loteAssinado):
        return self._validar(
                os.path.join(self._folder, self._pedidoEnviarLote),
                loteAssinado)

    def _validar(self, xsd, value):
        self._nfse = value
        xmlschema_doc = etree.parse(xsd)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        # Valida o XML como será enviado (serializado e lido de novo). O signxml
        # cria a Signature sem namespace na árvore em memória e depende só da
        # declaração xmlns, que só vale depois de serializar.
        r = xmlschema.validate(etree.fromstring(etree.tostring(value)))
        self._erros = xmlschema.error_log
        return r

    def setSchema(self, value):
        self._schema = value

    @property
    def erros(self):
        return self._erros 

    @property 
    def schema(self):
        return self._schema 

    @property
    def _pedidoEnviarLote(self):
        if self.schema == '1':
            return "PedidoEnvioLoteRPS_v01.xsd"
        return "PedidoEnvioLoteRPS_v02.xsd"
