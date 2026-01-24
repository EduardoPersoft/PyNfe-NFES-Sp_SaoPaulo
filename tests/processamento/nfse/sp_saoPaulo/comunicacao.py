import unittest
from lxml import etree
from pynfe.processamento.nfse import envelope
from pynfe.processamento.nfse.sp_saoPaulo import serializacao
from pynfe.processamento.nfse.sp_saoPaulo import metodos
from pynfe.processamento.nfse.sp_saoPaulo import comunicacao
from tests.test_nfse_serializacao import SerializacaoNFSeTest

class Metodos(unittest.TestCase):

    def test_envioLote(self):
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        nfse.simples = 2
        s = serializacao.Serializacao()
        x = s.gerar(nfse)
        m = metodos.Metodos()
        self.assertEqual(
                self._get_metodoEnviarLote(),
                etree.tostring(m.enviarLote(x), encoding="unicode", pretty_print=False))

    def test_envioLoteSimples(self):
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        s = serializacao.Serializacao()
        x = s.gerar(nfse)
        m = metodos.Metodos()
        m.setSchema('1')
        self.assertEqual(
                self._get_metodoEnviarLoteSimples(),
                etree.tostring(m.enviarLote(x), encoding="unicode", pretty_print=False))

    def test_envioTesteLote(self):
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        nfse.simples = 2
        s = serializacao.Serializacao()
        x = s.gerar(nfse)
        m = metodos.Metodos()
        self.assertEqual(
                self._get_metodoTestEnviarLote(),
                etree.tostring(m.enviarLote(x, homologacao=True), encoding="unicode", pretty_print=False))
    
    def test_EnvelopeEnviarLote(self):
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        nfse.simples = 2
        s = serializacao.Serializacao()
        x = s.gerar(nfse)
        m = metodos.Metodos()
        e = envelope.Envelope()
        self.assertEqual(
                self._get_envelopeEnviarLote(),
                etree.tostring(e.envelopar(m.enviarLote(x)), encoding="unicode", pretty_print=False))

    def test_comunicacao(self):
        certificado="./tests/certificado.pfx"
        certificado_senha=bytes("123456", "utf-8")
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        nfse.simples = 2
        s = serializacao.Serializacao()
        x = s.gerar(nfse)
        m = metodos.Metodos()
        e = envelope.Envelope()
        c = comunicacao.Comunicacao(certificado, certificado_senha)
        erro = ''
        try:
            xfim = e.envelopar(m.enviarLote(x))
            r = c.enviar_lote(xfim)
        except Exception as e:
            erro = str(e)
        self.assertEqual(erro, "HTTPSConnectionPool(host='nfews.prefeitura.sp.gov.br', port=443): Max retries exceeded with url: /lotenfe.asmx (Caused by SSLError(SSLError(399, '[SSL: EE_KEY_TOO_SMALL] ee key too small (_ssl.c:3900)')))")
        
    def _get_envelopeEnviarLote(self) -> str:
        return SerializacaoNFSeTest.strip_xml(
            f"""
                <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
               {self._get_envioLoteResponse()}
               </soap:Body>
               </soap:Envelope>
            """)

    def _get_metodoTestEnviarLote(self) -> str:
        return SerializacaoNFSeTest.strip_xml(self._get_testEnvioLoteRPS())

    def _get_metodoEnviarLote(self) -> str:
        return SerializacaoNFSeTest.strip_xml(self._get_EnvioLoteRPS())

    def _get_metodoEnviarLoteSimples(self) -> str:
        return SerializacaoNFSeTest.strip_xml(self._get_EnvioLoteRPSSimples())

    def _get_envioLoteResponse(self) -> str:
        return f"""
            <EnvioLoteRPSRequest xmlns="http://www.prefeitura.sp.gov.br/nfe">
                <VersaoSchema>2</VersaoSchema>
                <MensagemXML>
                <![CDATA[{SerializacaoNFSeTest.strip_xml(self._get_pedidoEnvioLoteRPS2())}]]>
                </MensagemXML>
            </EnvioLoteRPSRequest>
            """

    def _get_testEnvioLoteRPS(self) -> str:
        return f"""
            <TesteEnvioLoteRPSRequest xmlns="http://www.prefeitura.sp.gov.br/nfe">
                <VersaoSchema>2</VersaoSchema>
                <MensagemXML>
                <![CDATA[{SerializacaoNFSeTest.strip_xml(self._get_pedidoEnvioLoteRPS())}]]>
                </MensagemXML>
            </TesteEnvioLoteRPSRequest>
            """

    def _get_EnvioLoteRPS(self) -> str:
        return f"""
            <EnvioLoteRPSRequest xmlns="http://www.prefeitura.sp.gov.br/nfe">
                <VersaoSchema>2</VersaoSchema>
                <MensagemXML>
                <![CDATA[{SerializacaoNFSeTest.strip_xml(self._get_pedidoEnvioLoteRPS())}]]>
                </MensagemXML>
            </EnvioLoteRPSRequest>
            """

    def _get_EnvioLoteRPSSimples(self) -> str:
        return f"""
            <EnvioLoteRPSRequest xmlns="http://www.prefeitura.sp.gov.br/nfe">
                <VersaoSchema>1</VersaoSchema>
                <MensagemXML>
                <![CDATA[{SerializacaoNFSeTest.strip_xml(self._get_pedidoEnvioLoteRPSSimples())}]]>
                </MensagemXML>
            </EnvioLoteRPSRequest>
            """

    def _get_EnvioLoteRPS2(self) -> str:
        return f"""
            <EnvioLoteRPSRequest xmlns="http://www.prefeitura.sp.gov.br/nfe">
                <VersaoSchema>1</VersaoSchema>
                <MensagemXML>
                {self._get_pedidoEnvioLoteRPS2()}
                </MensagemXML>
            </EnvioLoteRPSRequest>
            """

    def _get_pedidoEnvioLoteRPS(self) -> str:
        return """
            <PedidoEnvioLoteRPS xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.prefeitura.sp.gov.br/nfe">
                <Cabecalho Versao="2" xmlns="">
                    <CPFCNPJRemetente>
                        <CNPJ>45111111111100</CNPJ>
                    </CPFCNPJRemetente>
                    <transacao>true</transacao>
                    <dtInicio>2025-04-10</dtInicio>
                    <dtFim>2025-04-10</dtFim>
                    <QtdRPS>1</QtdRPS>
                </Cabecalho>
                <RPS xmlns="">
                    <Assinatura>12312312323123123</Assinatura>
                    <ChaveRPS>
                        <InscricaoPrestador>000000</InscricaoPrestador>
                        <SerieRPS>A1</SerieRPS>
                        <NumeroRPS>50</NumeroRPS>
                    </ChaveRPS>
                    <TipoRPS>RPS</TipoRPS>
                    <DataEmissao>2025-04-10</DataEmissao>
                    <StatusRPS>N</StatusRPS>
                    <TributacaoRPS>T</TributacaoRPS>
                    <ValorDeducoes>10.00</ValorDeducoes>
                    <ValorPIS>10.00</ValorPIS>
                    <ValorCOFINS>10.00</ValorCOFINS>
                    <ValorINSS>10.00</ValorINSS>
                    <ValorIR>10.00</ValorIR>
                    <ValorCSLL>10.00</ValorCSLL>
                    <CodigoServico>1234</CodigoServico>
                    <AliquotaServicos>10.00</AliquotaServicos>
                    <ISSRetido>true</ISSRetido>
                    <CPFCNPJTomador>
                        <CNPJ>99999999999999</CNPJ>
                    </CPFCNPJTomador>
                    <RazaoSocialTomador>NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL</RazaoSocialTomador>
                    <EnderecoTomador>
                        <Logradouro>Rua tal</Logradouro>
                        <NumeroEndereco>0</NumeroEndereco>
                        <ComplementoEndereco>Ao lado de lugar nenhum</ComplementoEndereco>
                        <Bairro>Centro</Bairro>
                        <Cidade>1234567</Cidade>
                        <UF>MG</UF>
                        <CEP>33257010</CEP>
                    </EnderecoTomador>
                    <Discriminacao>Mensalidade</Discriminacao>
                    <ValorFinalCobrado>10.00</ValorFinalCobrado>
                    <ValorIPI>0.00</ValorIPI>
                    <ExigibilidadeSuspensa>1</ExigibilidadeSuspensa>
                    <PagamentoParceladoAntecipado>1</PagamentoParceladoAntecipado>
                    <NBS>115013000</NBS>
                    <cLocPrestacao>1234567</cLocPrestacao>
                    <IBSCBS>
                        <finNFSe>0</finNFSe>
                        <indFinal>0</indFinal>
                        <cIndOp>100301</cIndOp>
                        <tpOper>5</tpOper>
                        <indDest>1</indDest>
                        <valores>
                            <trib>
                                <gIBSCBS>
                                    <cClassTrib>200028</cClassTrib>
                                </gIBSCBS>
                            </trib>
                        </valores>
                    </IBSCBS>
                </RPS>
            </PedidoEnvioLoteRPS>
            """

    def _get_pedidoEnvioLoteRPSSimples(self) -> str:
        return """
            <PedidoEnvioLoteRPS xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.prefeitura.sp.gov.br/nfe">
                <Cabecalho Versao="1" xmlns="">
                    <CPFCNPJRemetente>
                        <CNPJ>45111111111100</CNPJ>
                    </CPFCNPJRemetente>
                    <transacao>true</transacao>
                    <dtInicio>2025-04-10</dtInicio>
                    <dtFim>2025-04-10</dtFim>
                    <QtdRPS>1</QtdRPS>
                    <ValorTotalServicos>10.00</ValorTotalServicos>
                    <ValorTotalDeducoes>10.00</ValorTotalDeducoes>
                </Cabecalho>
                <RPS xmlns="">
                    <Assinatura>12312312323123123</Assinatura>
                    <ChaveRPS>              
                        <InscricaoPrestador>00000000</InscricaoPrestador>
                        <SerieRPS>A1</SerieRPS>
                        <NumeroRPS>50</NumeroRPS>
                    </ChaveRPS>
                    <TipoRPS>RPS</TipoRPS>
                    <DataEmissao>2025-04-10</DataEmissao>
                    <StatusRPS>N</StatusRPS>
                    <TributacaoRPS>T</TributacaoRPS>
                    <ValorServicos>10.00</ValorServicos>
                    <ValorDeducoes>10.00</ValorDeducoes>
                    <ValorPIS>10.00</ValorPIS>
                    <ValorCOFINS>10.00</ValorCOFINS>
                    <ValorINSS>10.00</ValorINSS>
                    <ValorIR>10.00</ValorIR>
                    <ValorCSLL>10.00</ValorCSLL>
                    <CodigoServico>1234</CodigoServico>
                    <AliquotaServicos>10.00</AliquotaServicos>
                    <ISSRetido>true</ISSRetido>
                    <CPFCNPJTomador>
                        <CNPJ>99999999999999</CNPJ>
                    </CPFCNPJTomador>
                    <RazaoSocialTomador>NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL</RazaoSocialTomador>
                    <EnderecoTomador>
                        <Logradouro>Rua tal</Logradouro>
                        <NumeroEndereco>0</NumeroEndereco>
                        <ComplementoEndereco>Ao lado de lugar nenhum</ComplementoEndereco>
                        <Bairro>Centro</Bairro>
                        <Cidade>1234567</Cidade>
                        <UF>MG</UF>
                        <CEP>33257010</CEP>
                    </EnderecoTomador>
                    <Discriminacao>Mensalidade</Discriminacao>
                </RPS>
            </PedidoEnvioLoteRPS>
            """

    def _get_pedidoEnvioLoteRPS2(self) -> str:
        return """
            <PedidoEnvioLoteRPS xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.prefeitura.sp.gov.br/nfe">
                <Cabecalho Versao="2" xmlns="">
                    <CPFCNPJRemetente>
                        <CNPJ>45111111111100</CNPJ>
                    </CPFCNPJRemetente>
                    <transacao>true</transacao>
                    <dtInicio>2025-04-10</dtInicio>
                    <dtFim>2025-04-10</dtFim>
                    <QtdRPS>1</QtdRPS>
                </Cabecalho>
                <RPS xmlns="">
                    <Assinatura>12312312323123123</Assinatura>
                    <ChaveRPS>
                        <InscricaoPrestador>000000</InscricaoPrestador>
                        <SerieRPS>A1</SerieRPS>
                        <NumeroRPS>50</NumeroRPS>
                    </ChaveRPS>
                    <TipoRPS>RPS</TipoRPS>
                    <DataEmissao>2025-04-10</DataEmissao>
                    <StatusRPS>N</StatusRPS>
                    <TributacaoRPS>T</TributacaoRPS>
                    <ValorDeducoes>10.00</ValorDeducoes>
                    <ValorPIS>10.00</ValorPIS>
                    <ValorCOFINS>10.00</ValorCOFINS>
                    <ValorINSS>10.00</ValorINSS>
                    <ValorIR>10.00</ValorIR>
                    <ValorCSLL>10.00</ValorCSLL>
                    <CodigoServico>1234</CodigoServico>
                    <AliquotaServicos>10.00</AliquotaServicos>
                    <ISSRetido>true</ISSRetido>
                    <CPFCNPJTomador>
                        <CNPJ>99999999999999</CNPJ>
                    </CPFCNPJTomador>
                    <RazaoSocialTomador>NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL</RazaoSocialTomador>
                    <EnderecoTomador>
                        <Logradouro>Rua tal</Logradouro>
                        <NumeroEndereco>0</NumeroEndereco>
                        <ComplementoEndereco>Ao lado de lugar nenhum</ComplementoEndereco>
                        <Bairro>Centro</Bairro>
                        <Cidade>1234567</Cidade>
                        <UF>MG</UF>
                        <CEP>33257010</CEP>
                    </EnderecoTomador>
                    <Discriminacao>Mensalidade</Discriminacao>
                    <ValorFinalCobrado>10.00</ValorFinalCobrado>
                    <ValorIPI>0.00</ValorIPI>
                    <ExigibilidadeSuspensa>1</ExigibilidadeSuspensa>
                    <PagamentoParceladoAntecipado>1</PagamentoParceladoAntecipado>
                    <NBS>115013000</NBS>
                    <cLocPrestacao>1234567</cLocPrestacao>
                    <IBSCBS>
                        <finNFSe>0</finNFSe>
                        <indFinal>0</indFinal>
                        <cIndOp>100301</cIndOp>
                        <tpOper>5</tpOper>
                        <indDest>1</indDest>
                        <valores>
                            <trib>
                                <gIBSCBS>
                                    <cClassTrib>200028</cClassTrib>
                                </gIBSCBS>
                            </trib>
                        </valores>
                    </IBSCBS>
                </RPS>
            </PedidoEnvioLoteRPS>
            """

if __name__ == "__main__":
    unittest.main()
