NAMESPACE_NFSE = "http://www.sped.fazenda.gov.br/nfse"
VERSAO_DPS = "1.01"
VERSAO_APLICATIVO = "PyNFe"

# Fuso usado quando data_emissao não tem tzinfo (horário de Brasília).
FUSO_HORARIO_PADRAO = "-03:00"

URL_PRODUCAO = "https://sefin.nfse.gov.br/SefinNacional"
# Produção restrita. Não consta no swagger.json; host confirmado pela
# URL http://sefin.producaorestrita.nfse.gov.br/SefinNacional/DANFSe.
URL_HOMOLOGACAO = "https://sefin.producaorestrita.nfse.gov.br/SefinNacional"

TIPO_AMBIENTE_PRODUCAO = "1"
TIPO_AMBIENTE_HOMOLOGACAO = "2"

# tpEmit
EMITENTE_PRESTADOR = 1

# opSimpNac
SIMPLES_NAO_OPTANTE = 1
SIMPLES_MEI = 2
SIMPLES_ME_EPP = 3

# Faixa de série da DPS para emissão com aplicativo próprio (regra E0010)
SERIE_APLICATIVO_PROPRIO_MIN = 1
SERIE_APLICATIVO_PROPRIO_MAX = 49999

# Eventos
EVENTO_CANCELAMENTO = 101101
# Código de justificativa de cancelamento (cMotivo do e101101)
CANCELAMENTO_ERRO_EMISSAO = 1
CANCELAMENTO_SERVICO_NAO_PRESTADO = 2
CANCELAMENTO_OUTROS = 9

# Tipo de inscrição federal usado no Id da DPS
TIPO_INSCRICAO_CPF = "1"
TIPO_INSCRICAO_CNPJ = "2"
