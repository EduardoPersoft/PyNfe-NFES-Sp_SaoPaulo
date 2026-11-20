import os
from lxml import etree
from pynfe.utils import CAMINHO_DATA
from pynfe.processamento.nfse.nfse_nacional.flags import VERSAO_DPS


class Validacao(object):

    def __init__(self, versao=VERSAO_DPS):
        self._folder = os.path.join(CAMINHO_DATA, 'XSDs', 'NFS-e',
                                    'nfse_nacional', versao)
        self._versao = versao
        self._erros = None

    def validarDPS(self, dps):
        return self._validar(
                os.path.join(self._folder, f'DPS_v{self._versao}.xsd'), dps)

    def _validar(self, xsd, value):
        xmlschema = etree.XMLSchema(etree.parse(xsd))
        # Valida o XML como será enviado (serializado e lido de novo). O
        # signxml cria a Signature sem namespace na árvore em memória.
        r = xmlschema.validate(etree.fromstring(etree.tostring(value)))
        self._erros = xmlschema.error_log
        return r

    @property
    def erros(self):
        return self._erros
