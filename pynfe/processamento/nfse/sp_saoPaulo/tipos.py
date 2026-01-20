class Tipos(object):

    def __init__(self, nfse):
        self._nfse = nfse


    @property
    def tipoRPS(self):
        if self._nfse.tipo=='3':
            return "RPS-C"
        if self._nfse.tipo=='2':
            return "RPS-M"
        if self._nfse.tipo=='1':
            return "RPS"
        return ""

    @property
    def tributacaoRPS(self):
        if self._nfse.natureza_operacao == 1:
            return 'T'
        if self._nfse.natureza_operacao == 2:
            return 'F'
        if self._nfse.natureza_operacao == 3:
            return 'A'
        if self._nfse.natureza_operacao == 4:
            return 'M'
        if self._nfse.natureza_operacao == 5:
            return 'X'
        if self._nfse.natureza_operacao == 7:
            return 'B'
        if self._nfse.natureza_operacao == 8:
            return 'D'
        if self._nfse.natureza_operacao == 9:
            return 'N'
        if self._nfse.natureza_operacao == 10:
            return 'R'
        if self._nfse.natureza_operacao == 11:
            return 'S'
        if self._nfse.natureza_operacao == 12:
            return 'V'
        if self._nfse.natureza_operacao == 13:
            return 'V'
        return ""

    @property
    def exigibiliadeSuspensa(self):
        if self._nfse.natureza_operacao == 5:
            return 1 
        if self._nfse.natureza_operacao == 13:
            return 1 
        return 0
        
    @property
    def issRetidoSN(self):
        if self._nfse.servico.valor_iss_retido>0:
            return 'S'
        return 'N'

    @property
    def issRetido(self):
        if self._nfse.servico.valor_iss_retido>0:
            return 'true'
        return 'false'

    @property
    def documentoTomador(self):
        if self._nfse.cliente.tipo_documento=='CPF':
            return '1'
        return '2'
