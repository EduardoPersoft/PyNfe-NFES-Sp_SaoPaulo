import requests
from pynfe.entidades.certificado import CertificadoA1


class Comunicacao(object):

    def __init__(self, certificado, certificado_senha, homologacao=False):
        self._certificado = certificado
        self._certificado_senha = certificado_senha
        self._homologacao = homologacao

    def enviar_lote(self, xml):
        self._acao = 'enviar_lote'
        self._xml = xml
        return self._post()

    def _post_header(self):
        response = {
            "Content-Type": "text/xml; charset=utf-8;",
            "Content-Length": str(len(self.xml)),
            "SOAPAction": "http://www.prefeitura.sp.gov.br/nfe/ws/testeenvio"
        }
        return response
    
    def _post(self, timeout=None):
        certificado_a1 = CertificadoA1(self._certificado)
        chave, cert = certificado_a1.separar_arquivo(
                        self._certificado_senha, caminho=True)
        chave_cert = (cert, chave)
        try:
            result = requests.post(
                self.url,
                self.xml,
                headers=self._post_header(),
                cert=chave_cert,
                verify=True,
                timeout=timeout,
            )
            print(self.xml)
            result.encoding = "utf-8"
            return result
        except requests.exceptions.RequestException as e:
            raise e
        finally:
            certificado_a1.excluir()

    @property
    def url(self):
        return ''

    @property
    def xml(self):
        return self._xml


