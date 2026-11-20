NAMESPACE_NFSE = "http://www.sped.fazenda.gov.br/nfse"
VERSAO_DPS = "1.01"
VERSAO_APLICATIVO = "PyNFe"

# Fuso usado quando data_emissao não tem tzinfo (horário de Brasília).
FUSO_HORARIO_PADRAO = "-03:00"

URL_PRODUCAO = "https://sefin.nfse.gov.br/SefinNacional"
# A confirmar: não consta no swagger.json.
URL_HOMOLOGACAO = "https://sefin.producaorestrita.nfse.gov.br/SefinNacional"

TIPO_AMBIENTE_PRODUCAO = "1"
TIPO_AMBIENTE_HOMOLOGACAO = "2"

# tpEmit
EMITENTE_PRESTADOR = 1

# opSimpNac
SIMPLES_NAO_OPTANTE = 1
SIMPLES_MEI = 2
SIMPLES_ME_EPP = 3

# Tipo de inscrição federal usado no Id da DPS
TIPO_INSCRICAO_CPF = "1"
TIPO_INSCRICAO_CNPJ = "2"
