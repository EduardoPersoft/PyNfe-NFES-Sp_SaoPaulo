class Resposta(object):

    def __init__(self, retorno):
        self._retorno = retorno
        self._chkErros()
        self._alertas = self._getAlertas()
        self._rps = self._getRPS()

    def _getRPS(self):
        r = {}
        _chaves = self._retorno['RetornoEnvioLoteRPS']['ChaveNFeRPS']
        if not isinstance(_chaves, list):
            _chaves = [_chaves]
        for c in _chaves:
            _rps = c['ChaveRPS']['NumeroRPS']
            r[_rps] = {}
            r[_rps]['NFe'] = c['ChaveNFe']['NumeroNFe']
            r[_rps]['codigoVerificacao'] = c['ChaveNFe']['CodigoVerificacao']
            r[_rps]['chaveNFe'] = self._getChaveNFeNacional(c) 
            r[_rps]['urlNFSe'] = self._url(c['ChaveNFe']['InscricaoPrestador'],
                                           c['ChaveNFe']['NumeroNFe'],
                                           c['ChaveNFe']['CodigoVerificacao'])
        return r

    def _getChaveNFeNacional(self, chaveNFSe):
        c = chaveNFSe
        if c['ChaveNFe'].get('ChaveNotaFiscalNacional'):
            return c['ChaveNFe']['ChaveNotaFiscalNacional']
        return None

    def _getAlertas(self):
        r = []
        if not self._retorno['RetornoEnvioLoteRPS'].get('Alerta'):
            return r
        _alertas = self._retorno['RetornoEnvioLoteRPS']['Alerta']
        if not isinstance(_alertas, list):
            _alertas = [_alertas]
        for a in _alertas:
            r.append({'RPS': a['ChaveRPS']['NumeroRPS'],
                      'codigo': a['Codigo'],
                      'descricao': a['Descricao']}) 
        return r

    def _chkErros(self):
        r = []
        if not self._retorno['RetornoEnvioLoteRPS'].get('Erro'):
            return None 
        _erros = self._retorno['RetornoEnvioLoteRPS']['Erro']
        if not isinstance(_erros, list):
            _erros = [_erros]
        for a in _erros:
            r.append(f"{a['Codigo']} {a['Descricao']}")
        raise Exception('\n'.join(r))
    
    @property
    def rps(self):
        return self._rps

    @property
    def alertas(self):
        return self._alertas 


    def _url(self, inscricao, nfe, cdSeguranca):
        return f'https://nfe.prefeitura.sp.gov.br/nfe.aspx?ccm={inscricao}&nf={nfe}&cod={cdSeguranca}'
