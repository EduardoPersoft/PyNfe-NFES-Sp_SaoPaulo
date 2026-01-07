from lxml import etree

class Validacao(object):

    def __init__(self):
        self._folder = 'pynfe/data/XSDs/NFS-e/sp_saoPaulo/' 
        
    def validarLote(self, loteAssinado):
        return self._validar(
                f'{self._folder}{self._pedidoEnviarLote}',
                loteAssinado)

    def _validar(self, xsd, value):
        xmlschema_doc = etree.parse(xsd)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        r = xmlschema.validate(value)
        self._erros = xmlschema.error_log
        return r

    @property
    def erros(self):
        return self._erros 

    @property
    def _pedidoEnviarLote(self):
        return "PedidoEnvioLoteRPS_v02.xsd"
