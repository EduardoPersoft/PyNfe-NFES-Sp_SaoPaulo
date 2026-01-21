from lxml import etree
from pynfe.processamento.nfse import comunicacao

class Comunicacao(comunicacao.Comunicacao):

    @property
    def url(self):
        return 'https://nfews.prefeitura.sp.gov.br/lotenfe.asmx'

    @property
    def xml(self):
        _xml =etree.tostring(self._xml, encoding="unicode").replace("\n","")
        return f'<?xml version="1.0" encoding="UTF-8"?>{_xml}'

