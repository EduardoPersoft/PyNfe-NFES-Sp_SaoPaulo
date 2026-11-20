# Sobre o projeto

- O PyNFe é um software de terceiros, com licença livre, que oferece funcionalidades de emissão, cancelamento, registro de eventos e distribuição de NF-e e documentos afins.
- A emissão de NFS-e na versão original é limitada; hoje usamos dois sistemas proprietários para emitir NFS-e.
- Desenvolvemos uma extensão para emissão de NFS-e na Prefeitura de São Paulo, que já está em produção.
- Futuramente, quando tivermos mais segurança, vamos submeter essa funcionalidade à validação dos mantenedores do projeto.

# Situação atual

- Empresas enquadradas no Simples Nacional não podem usar as APIs da Prefeitura de São Paulo; elas devem usar o Portal Nacional da NFS-e.
- Precisamos implementar a emissão pelo Portal Nacional.
- Observação: o código ainda mantém, para São Paulo, o caminho do schema v01 usado por empresas do Simples (`simples == 1`).

# Estrutura do módulo de NFS-e

Caminho: `pynfe/processamento/nfse/`

## Arquivos comuns

- `autorizador.py`
    - `get(cidade, certificado, senha, nfse_nacional=False)`: recebe o **código IBGE** do município, o caminho do certificado A1 e a senha, e devolve o objeto de serviços da integração correspondente. Com `nfse_nacional=True` devolve a integração da NFS-e Nacional, qualquer que seja o município.
    - Municípios implementados: São Paulo (`3550308`). Para os demais, gera `Exception("Cidade não implementada!")`.
- `envelope.py`
    - `Envelope.envelopar(dados)`: cria um envelope SOAP 1.1 (`http://schemas.xmlsoap.org/soap/envelope/`) com os dados no `Body`.
- `comunicacao.py`
    - Classe base `Comunicacao`: faz o POST HTTPS com o certificado A1 (separa chave e certificado em arquivos temporários e os exclui ao final).
    - As subclasses de cada município definem `url` e `xml`.
- `validacao.py`
    - Vazio no momento.
- `compactador.py`
    - Classe `Compactador`: compacta XML em GZip com base64 e faz o caminho inverso, como exige a API da NFS-e Nacional.
    - Fica aqui, e não em `pynfe/utils/`, para manter nossas alterações isoladas no módulo até a validação pelo mantenedor, facilitando o merge.

## Integração Nacional (`nfse_nacional/`)

Em desenvolvimento: emissão e consultas implementadas, ainda não testadas em homologação. É escolhida pelo parâmetro `nfse_nacional=True` do `autorizador.get`. Detalhes em `nfse_nacional/README.md`.

## Integração de São Paulo (`sp_saoPaulo/`)

Cada integração de município fica em uma pasta própria, com a mesma organização.

- `servicos.py`: ponto de entrada da integração (classe `Servicos`).
- `assinaturaRPS.py`: monta a string de assinatura do RPS exigida por São Paulo e a assina (RSA, PKCS#1 v1.5, SHA-1).
- `serializacao.py`: gera o XML `PedidoEnvioLoteRPS` (cabeçalho e RPS).
- `validacao.py`: valida o lote com o XSD (`PedidoEnvioLoteRPS_v01.xsd` ou `_v02.xsd`, em `pynfe/data/XSDs/NFS-e/sp_saoPaulo/`).
- `metodos.py`: monta a requisição SOAP (`EnvioLoteRPSRequest` ou `TesteEnvioLoteRPSRequest`) com `VersaoSchema` e o XML em `MensagemXML` (CDATA).
- `comunicacao.py`: define a URL (`https://nfews.prefeitura.sp.gov.br/lotenfe.asmx`) e o XML enviado.
- `resposta.py`: interpreta o retorno, levanta exceção em caso de `Erro` e coleta alertas e chaves das NFS-e.
- `tipos.py`: converte os campos da nota para os códigos de São Paulo (tipo de RPS, tributação, ISS retido, documento do tomador).
- `flags.py`: namespaces e versões de schema.

### `Servicos.enviarLote(nfse, homologacao=False)`

Recebe uma NFS-e ou uma lista de NFS-e e executa, nesta ordem:

1. Define o schema: `simples == 1` usa o schema v01 (Simples); os demais usam o v02.
2. Assina cada RPS (exigência de São Paulo).
3. Serializa o lote em XML.
4. Assina o XML com o certificado A1.
5. Valida o XML com o XSD. Se for inválido, levanta `Exception` com a lista de erros e **não envia** o lote.
6. Monta o envelope SOAP e envia.
7. Interpreta o retorno.

Ambiente:

- `homologacao=False`: produção (`EnvioLoteRPS`), emite as notas.
- `homologacao=True`: usa `TesteEnvioLoteRPS`, que apenas valida o lote na prefeitura e **não emite** notas.

Retorno: um dicionário indexado pelo número do RPS:

```python
{
    '1': {
        'NFe': '8301',
        'codigoVerificacao': '85KJGFGG',
        'chaveNFe': None,  # chave da nota nacional, quando a prefeitura informa
        'urlNFSe': 'https://nfe.prefeitura.sp.gov.br/nfe.aspx?ccm=...&nf=8301&cod=85KJGFGG',
    }
}
```

Se o retorno tiver `Erro`, levanta `Exception` com o código e a descrição de cada erro. Os alertas (`Alerta`) são coletados em `Resposta.alertas`, mas ainda não são devolvidos por `enviarLote`.

### Exemplo de uso

```python
from pynfe.processamento.nfse import autorizador

servicos = autorizador.get('3550308', '/caminho/certificado.pfx', 'senha')
resultado = servicos.enviarLote(nfse, homologacao=True)
```
