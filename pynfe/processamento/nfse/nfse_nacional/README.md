# NFS-e Nacional (Sefin Nacional)

Integração com a API da Sefin Nacional para emissão de NFS-e pelo Portal Nacional.

## Motivação

- Empresas enquadradas no Simples Nacional não podem usar as APIs da Prefeitura de São Paulo e devem emitir pelo Portal Nacional da NFS-e.
- Esta integração segue a mesma organização de `sp_saoPaulo/` (veja `../README.md`).

## Situação

Em desenvolvimento. Já existem a serialização da DPS (leiaute 1.01), a assinatura, a validação com o XSD e o compactador. As seções marcadas com **(a implementar)** descrevem o plano, não código existente.

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

# Estrutura do módulo

Caminho: `pynfe/processamento/nfse/nfse_nacional/`

- `servicos.py` (a implementar): ponto de entrada (classe `Servicos`).
    - `enviar(nfse, homologacao=False)`
    - `consultar(chaveAcesso)`
    - `consultarDps(idDps)`
    - `cancelar(...)` e consulta de eventos
- `serializacao.py` (implementado): gera o XML da DPS. Veja "Serialização da DPS".
- `assinatura.py` (implementado): assina a DPS. Veja "Assinatura da DPS".
- `validacao.py` (implementado): `Validacao(versao='1.01').validarDPS(dps)` valida a DPS com o XSD; os erros ficam em `erros`.
- `comunicacao.py` (a implementar): requisições JSON por HTTPS com o certificado A1. A compactação usa `../compactador.py`.
- `resposta.py` (a implementar): interpreta os dois formatos de erro, devolve os alertas e descompacta o XML da NFS-e.
- `flags.py` (implementado): URLs dos ambientes, namespace, versões e códigos usados na DPS.

## Serialização da DPS

```python
from pynfe.processamento.nfse.nfse_nacional import serializacao

dps = serializacao.Serializacao().gerar(nfse, homologacao=False)  # etree._Element, sem assinatura
```

Gera a DPS no leiaute 1.01 a partir de um `NotaFiscalServico`. Por enquanto cobre o núcleo da DPS: identificação, prestador, tomador, serviço, valores, ISSQN, retenções federais e o grupo básico de IBS/CBS. Ainda não cobre substituição de NFS-e, intermediário, comércio exterior, obra, evento, deduções/reduções, benefício municipal, PIS/COFINS e o detalhamento de IBS/CBS.

### Identificação

| Campo | Origem |
|---|---|
| `infDPS/@Id` | `"DPS"` + `cLocEmi` (7) + tipo de inscrição (1 = CPF, 2 = CNPJ) + CNPJ/CPF do emitente (14, zeros à esquerda) + `serie` (5) + `nDPS` (15) |
| `tpAmb` | parâmetro `homologacao` (1 produção, 2 homologação) |
| `dhEmi` | `data_emissao`. Sem fuso (`tzinfo`), usa `-03:00` |
| `verAplic` | `"PyNFe"` |
| `serie` | `serie`. **Só números**, até 5 dígitos |
| `nDPS` | `identificador`, sem zeros à esquerda |
| `dCompet` | `data_competencia`; se não houver, a data de `data_emissao` |
| `tpEmit` | `tipo_emitente` (padrão 1, prestador) |
| `cLocEmi` | `emitente.endereco_cod_municipio` |

### Prestador (`prest`)

| Campo | Origem |
|---|---|
| `CNPJ` / `CPF` | `emitente.cnpj` (11 dígitos = CPF) |
| `IM` | `emitente.inscricao_municipal`, se houver |
| `xNome`, `end` | só quando `tipo_emitente` não é 1: com o prestador como emitente, vêm do cadastro nacional |
| `fone` | `emitente.endereco_telefone`, só os números |
| `email` | `emitente.email`, se houver |
| `regTrib/opSimpNac` | `op_simples_nacional`; se não houver, `simples == 1` vira 3 (ME/EPP) e os demais 1 (não optante). MEI (2) só pelo atributo |
| `regTrib/regApTribSN` | `regime_apuracao_sn`; padrão 1 quando `opSimpNac` é 3 |
| `regTrib/regEspTrib` | `regime_especial` (padrão 0) |

### Tomador (`toma`)

Só é gerado quando `nfse.cliente` existe.

| Campo | Origem |
|---|---|
| `CNPJ` / `CPF` | `cliente.numero_documento`, conforme `cliente.tipo_documento` |
| `IM` | `cliente.inscricao_municipal`, se houver |
| `xNome` | `cliente.razao_social` |
| `end` | endereço nacional do cliente, se `endereco_logradouro` estiver preenchido. `nro` vazio vira `S/N` |
| `fone`, `email` | `cliente.endereco_telefone`, `cliente.email` |

### Serviço (`serv`)

| Campo | Origem |
|---|---|
| `locPrest/cLocPrestacao` | `servico.codigo_municipio`; se vazio, o município do emitente |
| `cServ/cTribNac` | `servico.codigo_tributacao_nacional` (**obrigatório**, 6 dígitos) |
| `cServ/cTribMun` | `servico.codigo_tributacao_municipal_nacional` (3 dígitos), se houver. Não é o `codigo_tributacao_municipio` de São Paulo |
| `cServ/xDescServ` | `servico.discriminacao` |
| `cServ/cNBS` | `servico.nbs`, só os números |

### Valores (`valores`)

| Campo | Origem |
|---|---|
| `vServPrest/vServ` | `servico.valor_servico` |
| `vDescCondIncond` | `servico.desconto_incondicionado` e `desconto_condicionado`, quando maiores que zero |
| `trib/tribMun/tribISSQN` | `servico.tributacao_issqn` (padrão 1, operação tributável) |
| `trib/tribMun/tpRetISSQN` | `servico.tipo_retencao_issqn`; se não houver, `iss_retido == 1` vira 2 (retido pelo tomador) e os demais 1 (não retido) |
| `trib/tribMun/pAliq` | `servico.aliquota`, quando maior que zero |
| `trib/tribFed` | `vRetCP` = `valor_inss`, `vRetIRRF` = `valor_ir`, `vRetCSLL` = `valor_csll`, quando maiores que zero |
| `trib/totTrib` | `pTotTribSN` = `percentual_tributos_sn` se houver; senão `indTotTrib` = 0 |

### IBS/CBS (`IBSCBS`)

Só é gerado quando `IBSCBS_cIndOp` está preenchido. Usa os mesmos atributos do São Paulo: `IBSCBS_finNFSe`, `IBSCBS_indFinal`, `IBSCBS_cIndOp`, `IBSCBS_tpOper`, `IBSCBS_indDest` e `IBSCBS_cClassTrib`, mais `IBSCBS_CST` (3 dígitos), obrigatório no leiaute nacional.

### Atributos novos

Como em São Paulo, os campos que não existem nas entidades são atributos extras do `NotaFiscalServico` e do `Servico`, sem alterar `pynfe/entidades`:

- `NotaFiscalServico`: `data_competencia`, `tipo_emitente`, `op_simples_nacional`, `regime_apuracao_sn`, `percentual_tributos_sn`, `IBSCBS_CST`.
- `Servico`: `codigo_tributacao_nacional`, `codigo_tributacao_municipal_nacional`, `tributacao_issqn`, `tipo_retencao_issqn`.

## Assinatura da DPS

```python
from pynfe.processamento.nfse.nfse_nacional import assinatura

assinada = assinatura.Assinatura(certificado, senha).assinarDPS(dps)  # etree._Element
```

- XMLDSIG envelopada, com C14N inclusivo (`http://www.w3.org/TR/2001/REC-xml-c14n-20010315`).
- A `Reference` aponta para o `Id` do `infDPS` (`#DPS...`), e a `Signature` fica depois do `infDPS`, no namespace do XMLDSIG como padrão (sem prefixo `ds:`).
- RSA-SHA1 por padrão. `Assinatura(certificado, senha, algoritmo="sha256")` usa RSA-SHA256.
- Não remove acentos, ao contrário do `AssinaturaA1.assinar` da NF-e.
- Não altera a DPS recebida: devolve uma cópia assinada. Levanta `Exception` se a DPS não tiver `Id` ou já estiver assinada.

### Defeito no C14N do libxml2

A assinatura é montada no próprio `assinatura.py`, sem o signxml. O libxml2 2.14 (usado pelo lxml) calcula errado o C14N inclusivo de um trecho do documento: acrescenta `xmlns=""` em elementos que herdam o namespace padrão de um ancestral. Por exemplo, o C14N do `infDPS` sai com `<CNPJ xmlns="">`. O signxml depende desse C14N, então a assinatura gerada não confere com o C14N correto, que é o que a Sefin calcula. O verificador do signxml não percebe, porque usa o mesmo C14N com defeito.

Para contornar, o C14N é calculado sobre uma cópia do elemento como raiz do documento, o que dá o resultado correto. Os testes conferem o digest e a assinatura com um C14N independente do libxml2 (`xml.etree.ElementTree`).

O `AssinaturaA1.assinar` da NF-e não é afetado: ele relê o XML a partir do texto antes de assinar e usa `excise_empty_xmlns_declarations`, que remove os `xmlns=""` falsos do C14N. Conferido com o C14N independente (digest e assinatura). Com a DPS gerada em memória essa combinação não funcionou, por isso a assinatura própria.

### Correção no XSD 1.01

Em `tiposSimples_v1.01.xsd`, o padrão da série (`TSSerieDPS`) é `^0{0,4}\d{1,5}$`. Em XML Schema `^` e `$` não são âncoras, são caracteres literais, e o libxml2 recusa qualquer série. A cópia local foi corrigida para `0{0,4}\d{1,5}`, com um comentário no arquivo. **Ao atualizar os XSDs, refazer essa correção.**

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

- Obter o manual da NFS-e Nacional para conferir as regras de negócio usadas na serialização (formação do Id, prestador sem nome e endereço quando é o emitente, `regApTribSN`, `totTrib` e `pAliq` para o Simples) e o significado dos tipos de evento.
- Confirmar no manual o algoritmo de assinatura aceito (RSA-SHA1 ou RSA-SHA256).
- Confirmar a URL do ambiente de homologação.
- Incluir os XSDs no `package_data` do `setup.py` (hoje só `data/**/*.txt` é incluído).

# Testes

Ficam em `tests/processamento/nfse/nfse_nacional/`. Para rodar, a partir da raiz do projeto:

```
python -m tests.processamento.nfse.nfse_nacional.suite
```

- `compactador.py`: testes do `Compactador`.
- `assinatura.py`: testes da assinatura, com verificação independente do libxml2.
- `serializacao.py`: testes da serialização da DPS, incluindo a validação com o XSD 1.01. A função `get_nfse()` monta uma NFS-e de exemplo.
