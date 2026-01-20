import unittest
from lxml import etree

from pynfe.processamento.nfse.sp_saoPaulo import serializacao
from tests.test_nfse_serializacao import SerializacaoNFSeTest


class SerializacaoNFSesp_saoPaulo(unittest.TestCase):


    def test_gerar(self):
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        s = serializacao.Serializacao()
        x = s.gerar(nfse)
        self.assertEqual(
                self._get_lote_esperado(),
                etree.tostring(x, encoding="unicode", pretty_print=False))


    def _get_lote_esperado(self) -> str:
        return SerializacaoNFSeTest.strip_xml(f"""
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
            """)

                                              


    """
    <PedidoEnvioLoteRPS xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.prefeitura.sp.gov.br/nfe">
        <Cabecalho Versao="2" xmlns="">
            <CPFCNPJRemetente>
                <CNPJ>99999999000123</CNPJ>
            </CPFCNPJRemetente>
            <transacao>false</transacao>
            <dtInicio>2025-09-01</dtInicio>
            <dtFim>2025-10-20</dtFim>
            <QtdRPS>2</QtdRPS>
        </Cabecalho>
        <RPS xmlns="">
            <Assinatura>AbZN85C2TWp7f7RCvna8fBnAZwPAdWgTxWZyq11IkWJCMfWgHQy12Vwy55sq9cu/PgXEw7XJc0Cf3x1dttuKiF2Fz7Jzoj0BwL4h9mTfWrBnwgKQcje7/zFCKUHPCt8yoqAnbt4yfEP6+1eQ5UXUN4YuvvHg37uLhw/1mRgqgrOwe9SNio4np1ahhOwTCoBUi7bJ3fHU+Mm10uonulYq0YQS6n5Lme3+K1cipMjt7VN1erFoQM1FP5NwmlvLQbmbMR0w20WjAGnuISFnFlF/k+HOwDQLkteLfjJ6xdXAlJ5pioDkjfYOLqe5vw8zOjCdru6S+pyYwoiiztoUpynqkw==</Assinatura>
            <ChaveRPS>
                <InscricaoPrestador>99999999</InscricaoPrestador>
                <SerieRPS>ANNT4</SerieRPS>
                <NumeroRPS>152</NumeroRPS>
            </ChaveRPS>
            <TipoRPS>RPS</TipoRPS>
            <DataEmissao>2025-09-03</DataEmissao>
            <StatusRPS>N</StatusRPS>
            <TributacaoRPS>T</TributacaoRPS>
            <ValorDeducoes>0</ValorDeducoes>
            <ValorPIS>0</ValorPIS>
            <ValorCOFINS>0</ValorCOFINS>
            <ValorINSS>0</ValorINSS>
            <ValorIR>0</ValorIR>
            <ValorCSLL>0</ValorCSLL>
            <CodigoServico>1023</CodigoServico>
            <AliquotaServicos>0.05</AliquotaServicos>
            <ISSRetido>false</ISSRetido>
            <CPFCNPJTomador>
                <CNPJ>99999999999999</CNPJ>
            </CPFCNPJTomador>
            <RazaoSocialTomador>TESTE</RazaoSocialTomador>
            <EnderecoTomador>
                <TipoLogradouro>RUA</TipoLogradouro>
                <Logradouro>TESTE</Logradouro>
                <NumeroEndereco>0001</NumeroEndereco>
                <ComplementoEndereco>0101</ComplementoEndereco>
                <Bairro>TESTE</Bairro>
                <Cidade>3550308</Cidade>
                <UF>SP</UF>
                <CEP>4141500</CEP>
            </EnderecoTomador>
            <Discriminacao>teste geral IBS</Discriminacao>
            <ValorFinalCobrado>2300.65</ValorFinalCobrado>
            <ValorIPI>0</ValorIPI>
            <ExigibilidadeSuspensa>0</ExigibilidadeSuspensa>
            <PagamentoParceladoAntecipado>0</PagamentoParceladoAntecipado>
            <NBS>115013000</NBS>
            <cLocPrestacao>4114203</cLocPrestacao>
            <IBSCBS>
                <finNFSe>0</finNFSe>
                <indFinal>0</indFinal>
                <cIndOp>020101</cIndOp>
                <indDest>1</indDest>
                <dest>
                    <CNPJ>J0CM5ZAU000106</CNPJ>
                    <xNome>NOME TESTE</xNome>
                </dest>
                <valores>
                    <gReeRepRes>
                        <documentos>
                            <dFeNacional>
                                <tipoChaveDFe>9</tipoChaveDFe>
                                <xTipoChaveDFe>TesteChaveDFe</xTipoChaveDFe>
                                <chaveDFe>85296374108529637410852963741085296374108529637410</chaveDFe>
                            </dFeNacional>
                            <fornec>
                                <CNPJ>99999999000101</CNPJ>
                                <xNome>teste</xNome>
                            </fornec>
                            <dtEmiDoc>2025-09-02</dtEmiDoc>
                            <dtCompDoc>2025-09-01</dtCompDoc>
                            <tpReeRepRes>99</tpReeRepRes>
                            <xTpReeRepRes>Outros</xTpReeRepRes>
                            <vlrReeRepRes>123.00</vlrReeRepRes>
                        </documentos>
                    </gReeRepRes>
                    <trib>
                        <gIBSCBS>
                            <cClassTrib>000001</cClassTrib>
                        </gIBSCBS>
                    </trib>
                </valores>
                <imovelobra>
                    <end>
                        <CEP>4041020</CEP>
                        <xLgr>Rua Ouvidor Teste</xLgr>
                        <nro>232</nro>
                        <xBairro>Vila Teste</xBairro>
                    </end>
                </imovelobra>
            </IBSCBS>
        </RPS>
        <RPS xmlns="">
            <Assinatura>JfgC+ftqWj1m4vWIqLQHisfx7wmhktk969PM7ZEhbI2cc2+LnwGDoLivbK6F+o0JcLabZvUz9+fqOcopKYT1tpIKofYfTwl9EfPp0rQnsSX7DeN4FXdqKdu4PLG98h0mDiM7ZOqOlik88h+eyen44p8SnAEH1njXC1T+MDx6SpsD7/XKuT7Vn1dSXeq0Z0JDl282rDdZzBVhisyas0Dz++52S192bImxSKB0VjS5yGXT5Yd2oE9zexZkRNasveOARIJ/nher2UtkiY2ZSOys2qmMeLGas4avO5qWZVA6UAHzjedA5kc7997ebJ56aGPOISrBb3AUGX2ruM52DrZx7w==</Assinatura>
            <ChaveRPS>
                <InscricaoPrestador>99999999</InscricaoPrestador>
                <SerieRPS>ANNT4</SerieRPS>
                <NumeroRPS>153</NumeroRPS>
            </ChaveRPS>
            <TipoRPS>RPS</TipoRPS>
            <DataEmissao>2025-09-02</DataEmissao>
            <StatusRPS>N</StatusRPS>
            <TributacaoRPS>T</TributacaoRPS>
            <ValorDeducoes>0</ValorDeducoes>
            <ValorPIS>0</ValorPIS>
            <ValorCOFINS>0</ValorCOFINS>
            <ValorINSS>0</ValorINSS>
            <ValorIR>0</ValorIR>
            <ValorCSLL>0</ValorCSLL>
            <CodigoServico>1023</CodigoServico>
            <AliquotaServicos>0.05</AliquotaServicos>
            <ISSRetido>false</ISSRetido>
            <CPFCNPJTomador>
                <CNPJ>99999999000166</CNPJ>
            </CPFCNPJTomador>
            <RazaoSocialTomador>TESTE</RazaoSocialTomador>
            <EnderecoTomador>
                <TipoLogradouro>RUA</TipoLogradouro>
                <Logradouro>TESTE 2</Logradouro>
                <NumeroEndereco>100</NumeroEndereco>
                <ComplementoEndereco>Bloco A</ComplementoEndereco>
                <Bairro>TESTE</Bairro>
                <Cidade>3550308</Cidade>
                <UF>SP</UF>
                <CEP>4141500</CEP>
            </EnderecoTomador>
            <Discriminacao>teste geral IBS 2</Discriminacao>
            <ValorInicialCobrado>10000.98</ValorInicialCobrado>
            <ValorIPI>0</ValorIPI>
            <ExigibilidadeSuspensa>0</ExigibilidadeSuspensa>
            <PagamentoParceladoAntecipado>0</PagamentoParceladoAntecipado>
            <NBS>115029000</NBS>
            <cLocPrestacao>3550308</cLocPrestacao>
            <IBSCBS>
                <finNFSe>0</finNFSe>
                <indFinal>0</indFinal>
                <cIndOp>100301</cIndOp>
                <tpOper>5</tpOper>
                <tpEnteGov>1</tpEnteGov>
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
    """
    def test_notafiscal_geral(self):
        nfse = SerializacaoNFSeTest.get_notafiscal_servico()
        nfse_xml = self._serializa_nfse(nfse)

        nfse_xml_assinado = SerializacaoNFSeTest.assina_xml(nfse_xml)
        nfse_esperada = self._get_nfse_esperada()

        nfse_xml_assinado = self._ajusta_xml_test(nfse_xml_assinado)
        nfse_esperada = self._ajusta_xml_test(nfse_esperada)

        # Teste do conteúdo das tags do XML
        self.maxDiff = None
        self.assertEqual(nfse_xml_assinado, nfse_esperada)

        # Testa a validação do XML com os schemas XSD
        # SerializacaoNFSeTest.validacao_com_xsd_do_xml_gerado_sem_processar(
        #     nfse_xml,
        #     nfse_xml_assinado,
        #     'servico_enviar_lote_rps_envio_v03.xsd',
        #     'pynfe/data/XSDs/NFS-e/Ginfes'
        # )



        SerializacaoNFSeTest.limpa_namespace()

    def _serializa_nfse(self, nfse: NotaFiscalServico) -> str:
        serializador = SerializacaoNfse("ginfes")
        xml = serializador.gerar_lote(nfse)

        return xml

    # a serialização gera os atributos xmlns:ns1 e xmlns:ns2
    # da tag ns1:EnviarLoteRpsEnvio em ordem randômica (!!!)
    def _ajusta_xml_test(self, xml: str) -> str:
        return re.sub(r"<(ns1:EnviarLoteRpsEnvio)[^>]*>", r"<\1>", xml)

    """
    def _get_nfse_esperada(self) -> str:
        return SerializacaoNFSeTest.strip_xml(f"""
            <ns1:EnviarLoteRpsEnvio xmlns:ns1="http://www.ginfes.com.br/servico_enviar_lote_rps_envio_v03.xsd"
                xmlns:ns2="http://www.ginfes.com.br/tipos_v03.xsd">
                <ns1:LoteRps Id="1">
                    <ns2:NumeroLote>1</ns2:NumeroLote>
                    <ns2:Cnpj>45111111111100</ns2:Cnpj>
                    <ns2:InscricaoMunicipal>000000</ns2:InscricaoMunicipal>
                    <ns2:QuantidadeRps>1</ns2:QuantidadeRps>
                    <ns2:ListaRps>
                        <ns2:Rps>
                            <ns2:InfRps Id="50">
                                <ns2:IdentificacaoRps>
                                    <ns2:Numero>50</ns2:Numero>
                                    <ns2:Serie>A1</ns2:Serie>
                                    <ns2:Tipo>1</ns2:Tipo>
                                </ns2:IdentificacaoRps>
                                <ns2:DataEmissao>{SerializacaoNFSeTest.data_hora}</ns2:DataEmissao>
                                <ns2:NaturezaOperacao>1</ns2:NaturezaOperacao>
                                <ns2:OptanteSimplesNacional>1</ns2:OptanteSimplesNacional>
                                <ns2:IncentivadorCultural>2</ns2:IncentivadorCultural>
                                <ns2:Status>1</ns2:Status>
                                <ns2:Servico>
                                    <ns2:Valores>
                                        <ns2:ValorServicos>100.0</ns2:ValorServicos>
                                        <ns2:ValorDeducoes>10.0</ns2:ValorDeducoes>
                                        <ns2:ValorPis>10.0</ns2:ValorPis>
                                        <ns2:ValorCofins>10.0</ns2:ValorCofins>
                                        <ns2:ValorInss>10.0</ns2:ValorInss>
                                        <ns2:ValorIr>10.0</ns2:ValorIr>
                                        <ns2:ValorCsll>10.0</ns2:ValorCsll>
                                        <ns2:IssRetido>1</ns2:IssRetido>
                                        <ns2:ValorIss>10.0</ns2:ValorIss>
                                        <ns2:ValorIssRetido>10.0</ns2:ValorIssRetido>
                                        <ns2:OutrasRetencoes>10.0</ns2:OutrasRetencoes>
                                        <ns2:BaseCalculo>10.0</ns2:BaseCalculo>
                                        <ns2:Aliquota>10.0</ns2:Aliquota>
                                        <ns2:ValorLiquidoNfse>10.0</ns2:ValorLiquidoNfse>
                                        <ns2:DescontoIncondicionado>10.0</ns2:DescontoIncondicionado>
                                        <ns2:DescontoCondicionado>10.0</ns2:DescontoCondicionado>
                                    </ns2:Valores>
                                    <ns2:ItemListaServico>0101</ns2:ItemListaServico>
                                    <ns2:CodigoCnae>6201501</ns2:CodigoCnae>
                                    <ns2:CodigoTributacaoMunicipio>1234</ns2:CodigoTributacaoMunicipio>
                                    <ns2:Discriminacao>Mensalidade</ns2:Discriminacao>
                                    <ns2:CodigoMunicipio>3149309</ns2:CodigoMunicipio>
                                </ns2:Servico>
                                <ns2:Prestador>
                                    <ns2:Cnpj>45111111111100</ns2:Cnpj>
                                    <ns2:InscricaoMunicipal>000000</ns2:InscricaoMunicipal>
                                </ns2:Prestador>
                                <ns2:Tomador>
                                    <ns2:IdentificacaoTomador>
                                        <ns2:CpfCnpj>
                                            <ns2:Cnpj>99999999999999</ns2:Cnpj>
                                        </ns2:CpfCnpj>
                                        <ns2:InscricaoMunicipal>1234</ns2:InscricaoMunicipal>
                                    </ns2:IdentificacaoTomador>
                                    <ns2:RazaoSocial>NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL</ns2:RazaoSocial>
                                    <ns2:Endereco>
                                        <ns2:Endereco>Rua tal</ns2:Endereco>
                                        <ns2:Numero>0</ns2:Numero>
                                        <ns2:Complemento>Ao lado de lugar nenhum</ns2:Complemento>
                                        <ns2:Bairro>Centro</ns2:Bairro>
                                        <ns2:CodigoMunicipio>123</ns2:CodigoMunicipio>
                                        <ns2:Uf>MG</ns2:Uf>
                                        <ns2:Cep>33257010</ns2:Cep>
                                    </ns2:Endereco>
                                    <ns2:Contato>
                                        <ns2:Telefone>12365478945</ns2:Telefone>
                                        <ns2:Email>nome@email.com.br</ns2:Email>
                                    </ns2:Contato>
                                </ns2:Tomador>
                            </ns2:InfRps>
                        </ns2:Rps>
                    </ns2:ListaRps>
                </ns1:LoteRps>
                <Signature xmlns="http://www.w3.org/2000/09/xmldsig#">
                    <SignedInfo>
                        <CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>
                        <SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/>
                        <Reference URI="#1">
                            <Transforms>
                                <Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
                                <Transform Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>
                            </Transforms>
                            <DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/>
                            <DigestValue>1KzhiSjBh9Ka3slT/bpIlKyPEcI=</DigestValue>
                        </Reference>
                    </SignedInfo>
                    <SignatureValue>ZwLBWwIgp1UmNnNi1M1Eqeym1L3hc6Y4iaQlQE8qQnF+l5y0V0l78cbqnqnhhJ4Aus/g89UajSr/6pAKHJf242nWBjD7A4KYH9bbSkAh12W4n1wf5gpUrMPyQUlDhgCLOfCpOyzWnhofy+f7Tm1/Qws82JFUWs1jyJ9A5UyTbrU=</SignatureValue>
                    <KeyInfo>
                        <X509Data>
                            <X509Certificate>MIICMTCCAZqgAwIBAgIQfYOsIEVuAJ1FwwcTrY0t1DANBgkqhkiG9w0BAQUFADBX\nMVUwUwYDVQQDHkwAewA1ADkARgAxAEUANAA2ADEALQBEAEQARQA1AC0ANABEADIA\nRgAtAEEAMAAxAEEALQA4ADMAMwAyADIAQQA5AEUAQgA4ADMAOAB9MB4XDTE1MDYx\nNTA1NDc1N1oXDTE2MDYxNDExNDc1N1owVzFVMFMGA1UEAx5MAHsANQA5AEYAMQBF\nADQANgAxAC0ARABEAEUANQAtADQARAAyAEYALQBBADAAMQBBAC0AOAAzADMAMgAy\nAEEAOQBFAEIAOAAzADgAfTCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEAk41G\nnqXXLaiOC/y0/cA4tbS+NZCqI+x4EsztgDFvPPlHstiVYcLRkni4i93gK9zoC6g0\nmh66HMVzAfE8vRNwW5b7m6nWS1SiHBon7/Mqsw4MIq3SC+J/fTbKpqwyfAuH2YZl\nAiQuQc85fyllAMLh2WrA7JgOLR/5tF3kLtpbHdECAwEAATANBgkqhkiG9w0BAQUF\nAAOBgQArdh+RyT6VxKGsXk1zhHsgwXfToe6GpTF4W8PHI1+T0WIsNForDhvst6nm\nQtgAhuZM9rxpOJuNKc+pM29EixpAiZZiRMCSWEItNyEVdUIi+YnKBcAHd88TwO86\nd126MWQ2O8cu5W1VoDp7hYBYKOnLbYi11/StO+0rzK+oPYAvIw==\n</X509Certificate>
                        </X509Data>
                    </KeyInfo>
                </Signature>
            </ns1:EnviarLoteRpsEnvio>""")


if __name__ == "__main__":
    unittest.main()
