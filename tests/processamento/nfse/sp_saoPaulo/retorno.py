import unittest
from pynfe.processamento.nfse.sp_saoPaulo import resposta

RETORNO_LOTE_RPSUNICA = {'RetornoEnvioLoteRPS': {
                            '@xmlns:xsd': 'http://www.w3.org/2001/XMLSchema', 
                            '@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                            '@xmlns': 'http://www.prefeitura.sp.gov.br/nfe',
                            'Cabecalho': {
                                '@Versao': '1', '@xmlns': '', 'Sucesso': 'true', 
                                'InformacoesLote': {'NumeroLote': '1658603910', 
                                                    'InscricaoPrestador': '32415354', 
                                                    'CPFCNPJRemetente': {'CNPJ': '47294988000102'}, 
                                                    'DataEnvioLote': '2026-01-26T09:04:42', 
                                                    'QtdNotasProcessadas': '1', 
                                                    'TempoProcessamento': '0', 
                                                    'ValorTotalServicos': '2488.4'}
                                         }, 
                            'Alerta': {
                                '@xmlns': '', 
                                'Codigo': '307', 
                                'Descricao': 'Código de Serviço informado (2800) da NFS-e não está '
                                              'cadastrado para o prestador de serviço.', 
                                'ChaveRPS': {'InscricaoPrestador': '32415354', 
                                             'SerieRPS': '2', 
                                             'NumeroRPS': '10267'}
                                       }, 
                           'ChaveNFeRPS': {'@xmlns': '', 
                                           'ChaveNFe': {'InscricaoPrestador': '32415354',
                                                        'NumeroNFe': '8300',
                                                        'CodigoVerificacao': 'BWM4IXHB'},
                                           'ChaveRPS': {'InscricaoPrestador': '32415354', 
                                                        'SerieRPS': '2', 
                                                        'NumeroRPS': '10267'}
                                           }
                           }
                         }

class RetornoLoteRPS(unittest.TestCase):
    
    def test_alertLoteUnico(self):
        r = resposta.Resposta(RETORNO_LOTE_RPSUNICA)
        self.assertEqual(r.alertas[0]['RPS'], '10267')
        self.assertEqual(r.alertas[0]['codigo'], '307')
        self.assertEqual(r.alertas[0]['descricao'],
                         'Código de Serviço informado (2800) da NFS-e não está '
                         'cadastrado para o prestador de serviço.' )
        
    def test_rosLoteUnico(self):
        r = resposta.Resposta(RETORNO_LOTE_RPSUNICA)
        self.assertEqual(r.rps['10267']['NFe'], '8300')
        self.assertEqual(r.rps['10267']['codigoVerificacao'], 'BWM4IXHB')
        self.assertEqual(r.rps['10267']['chaveNFe'], None)
        self.assertEqual(r.rps['10267']['urlNFSe'], 'https://nfe.prefeitura.sp.gov.br/nfe.aspx?ccm=32415354&nf=8300&cod=BWM4IXHB')
        
if __name__=='__main__':
    unittest.main(verbosity=3)
