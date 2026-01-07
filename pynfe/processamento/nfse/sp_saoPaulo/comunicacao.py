from pynfe.processamento.nfse import comunicacao

class Comunicacao(comunicacao.Comunicacao):

    @property
    def url(self):
        return 'https://nfews.prefeitura.sp.gov.br'

    @property
    def xml(self):
        return f'<?xml version="1.0" encoding="UTF-8"?>{self._xml}'

