# NFS-e Nacional (Sefin Nacional)

Integração com a API da Sefin Nacional para emissão de NFS-e pelo Portal Nacional.

## Motivação

- Empresas enquadradas no Simples Nacional não podem usar as APIs da Prefeitura de São Paulo e devem emitir pelo Portal Nacional da NFS-e.
- Esta integração segue a mesma organização de `sp_saoPaulo/` (veja `../README.md`).

## Situação

Em desenvolvimento. Até agora existem apenas esta documentação e a especificação da API (`swagger.json`). As seções marcadas com **(a implementar)** descrevem o plano, não código existente.

# A API

Fonte: `swagger.json` (Swagger 2.0, "API NFS-e - Sefin Nacional", versão v1).

## Comunicação

- **Protocolo:** HTTPS com autenticação mútua (TLS 1.0, 1.1 e 1.2, segundo a especificação).
- **Autenticação:** somente o certificado digital ICP-Brasil (A1 ou A3, CNPJ ou CPF, com "Autenticação Cliente"). Não há token.
- **Mensagens:** JSON, codificação UTF-8.
- **Documentos:** a DPS, a NFS-e e os eventos são XML 1.0 assinados com XMLDSIG, compactados em GZip e codificados em base64 dentro do JSON.
- **Emissão síncrona, uma DPS por requisição.** Não há envio em lote como em São Paulo.

## Ambientes

| Ambiente | URL base | Situação |
|---|---|---|
| Produção | `https://sefin.nfse.gov.br/SefinNacional` | Consta na especificação |
| Homologação (produção restrita) | `https://sefin.producaorestrita.nfse.gov.br/SefinNacional` | **A confirmar**: não consta na especificação |

A especificação declara `schemes: ["http"]`, mas a comunicação real é HTTPS com certificado.

## Endpoints

| Método | Caminho | Uso | Retornos |
|---|---|---|---|
| `POST` | `/nfse` | Recepciona a DPS e gera a NFS-e | 201, 400, 403, 500 |
| `GET` | `/nfse/{chaveAcesso}` | Consulta a NFS-e pela chave de acesso (50 dígitos) | 200, 400, 401, 403, 404 |
| `GET` | `/dps/{id}` | Retorna a chave de acesso da NFS-e gerada a partir do Id da DPS | 200, 400, 404 |
| `HEAD` | `/dps/{id}` | Verifica se já existe NFS-e para o Id da DPS | 200, 400, 404 |
| `POST` | `/nfse/{chaveAcesso}/eventos` | Registra um evento (por exemplo, cancelamento) | 201, 400, 401 |
| `GET` | `/nfse/{chaveAcesso}/eventos/{tipoEvento}/{numSeqEvento}` | Consulta um evento | 200, 401, 404, 422 |

Endpoints que não serão usados:

- `GET /DANFSe` e `GET /ParametrosMunicipais`: respondem 501, pois foram movidos para o ADN (`adn.producaorestrita.nfse.gov.br`).
- `POST /decisao-judicial/nfse`: recepção de NFS-e gerada por decisão judicial.

Tipos de evento aceitos na consulta (`tipoEvento`): 101101, 101103, 105102, 105104, 105105, 202201, 202205, 203202, 203206, 204203, 204207, 205204, 205208, 305101, 305102, 305103, 467201, 907201.

## Requisições e respostas

### `POST /nfse`

Requisição:

```json
{ "dpsXmlGZipB64": "<DPS assinada, GZip, base64>" }
```

Sucesso (201):

```json
{
  "tipoAmbiente": 1,
  "versaoAplicativo": "...",
  "dataHoraProcessamento": "2026-11-20T17:28:45.7540134-03:00",
  "idDps": "...",
  "chaveAcesso": "...",
  "nfseXmlGZipB64": "<NFS-e, GZip, base64>",
  "alertas": [{ "codigo": "...", "descricao": "...", "complemento": "..." }]
}
```

Erro (400, 403, 500):

```json
{
  "tipoAmbiente": 1,
  "versaoAplicativo": "...",
  "dataHoraProcessamento": "...",
  "idDPS": "...",
  "erros": [{ "codigo": "...", "descricao": "...", "complemento": "..." }]
}
```

- 400: não foi possível criar a NFS-e.
- 403: certificado digital da transmissão inválido ou fora dos padrões.
- 500: falha durante o processamento da DPS.

### `POST /nfse/{chaveAcesso}/eventos`

Requisição: `{ "pedidoRegistroEventoXmlGZipB64": "..." }`

Sucesso (201): `tipoAmbiente`, `versaoAplicativo`, `dataHoraProcessamento` e `eventoXmlGZipB64`. A consulta de evento devolve a mesma estrutura.

### Consultas

- `GET /nfse/{chaveAcesso}` devolve `chaveAcesso` e `nfseXmlGZipB64`.
- `GET /dps/{id}` devolve `idDps` e `chaveAcesso`.

### Formatos de erro

A API usa dois formatos diferentes:

| Endpoint | Estrutura | Campo de erro |
|---|---|---|
| `POST /nfse` | `NFSePostResponseErro` | `erros` (lista) e `idDPS` |
| Demais | `ResponseErro` | `erro` (um objeto) |

Nos dois casos cada mensagem tem `codigo`, `descricao` e `complemento`. Em todas as respostas, `tipoAmbiente` é 1 para produção e 2 para homologação.

# Estrutura do módulo (a implementar)

Caminho: `pynfe/processamento/nfse/nfse_nacional/`

- `servicos.py`: ponto de entrada (classe `Servicos`).
    - `enviar(nfse, homologacao=False)`
    - `consultar(chaveAcesso)`
    - `consultarDps(idDps)`
    - `cancelar(...)` e consulta de eventos
- `serializacao.py`: gera o XML da DPS.
- `validacao.py`: valida a DPS com o XSD antes do envio, como em São Paulo.
- `comunicacao.py`: requisições JSON por HTTPS com o certificado A1. A compactação usa `../compactador.py`.
- `resposta.py`: interpreta os dois formatos de erro, devolve os alertas e descompacta o XML da NFS-e.
- `flags.py`: URLs dos ambientes, namespaces e versões.

## Fluxo de `enviar` (a implementar)

1. Serializa a DPS em XML.
2. Assina o XML com o certificado A1 (XMLDSIG).
3. Valida o XML com o XSD. Se for inválido, levanta `Exception` com a lista de erros e não envia.
4. Compacta em GZip, codifica em base64 e envia em `POST /nfse`.
5. Interpreta a resposta: em caso de sucesso devolve a chave de acesso, o Id da DPS, o XML da NFS-e e os alertas; em caso de erro levanta `Exception` com os códigos e descrições.

### Reenvio sem duplicar a NFS-e

Se o `POST /nfse` falhar por timeout ou queda de conexão, não há como saber se a NFS-e foi gerada. Antes de reenviar, consultar `GET /dps/{id}`:

- 200: a NFS-e já existe; usar a chave de acesso devolvida.
- 404: a NFS-e não foi gerada; é seguro reenviar.

## Seleção do serviço (a implementar)

O `autorizador.get` passa a receber o parâmetro `nfse_nacional` (padrão `False`):

```python
servicos = autorizador.get(cidade, certificado, senha, nfse_nacional=True)
```

- `nfse_nacional=True`: usa a integração do Portal Nacional (`nfse_nacional/`), qualquer que seja o município.
- `nfse_nacional=False`: mantém o comportamento atual, escolhendo a integração pelo código IBGE do município.

## Código comum no módulo de NFS-e

Como nosso código ainda não foi validado pelo mantenedor do PyNFe, as rotinas comuns ficam em `pynfe/processamento/nfse/` e não em `pynfe/utils/`. Assim as alterações ficam isoladas no módulo e o merge com o restante do projeto é mais simples.

- `compactador.py` (implementado): classe `Compactador`.
    - `compactar(xml)`: recebe `etree._Element`, `str` ou `bytes` e devolve uma `str` com o XML em UTF-8 compactado em GZip e codificado em base64. Um `etree._Element` é serializado com a declaração `<?xml ...?>`.
    - `descompactar(dados)`: recebe o base64 devolvido pela API e retorna o XML como `str`.
    - `descompactarXml(dados)`: o mesmo, retornando `etree._Element`.

# Pendências

- Obter os XSDs da NFS-e Nacional (DPS, NFS-e e eventos) e guardá-los em `pynfe/data/XSDs/NFS-e/nfse_nacional/`.
- Obter o manual da NFS-e Nacional: formação do Id da DPS e da chave de acesso, regras de negócio e significado dos tipos de evento.
- Confirmar a URL do ambiente de homologação.
- Incluir os XSDs no `package_data` do `setup.py` (hoje só `data/**/*.txt` é incluído).

# Testes

Ficam em `tests/processamento/nfse/nfse_nacional/`. Para rodar, a partir da raiz do projeto:

```
python -m tests.processamento.nfse.nfse_nacional.suite
```

- `compactador.py`: testes do `Compactador`.
