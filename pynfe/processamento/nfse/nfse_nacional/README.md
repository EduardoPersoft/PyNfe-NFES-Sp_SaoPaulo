# NFS-e Nacional (Sefin Nacional)

Integração com a API da Sefin Nacional para emissão de NFS-e pelo Portal Nacional.

## Motivação

- Empresas enquadradas no Simples Nacional não podem usar as APIs da Prefeitura de São Paulo e devem emitir pelo Portal Nacional da NFS-e.
- Esta integração segue a mesma organização de `sp_saoPaulo/` (veja `../README.md`).

## Situação

Em desenvolvimento. Já existem a serialização da DPS (leiaute 1.01), a assinatura, a validação com o XSD, o compactador e a comunicação com a Sefin (envio da DPS e consultas). Falta testar em homologação com um certificado real e implementar os eventos (cancelamento). As seções marcadas com **(a implementar)** descrevem o plano, não código existente.

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
| Homologação (produção restrita) | `https://sefin.producaorestrita.nfse.gov.br/SefinNacional` | Não consta na especificação; host confirmado pela URL `http://sefin.producaorestrita.nfse.gov.br/SefinNacional/DANFSe` |

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

- `servicos.py` (implementado): ponto de entrada (classe `Servicos`). Veja "Uso".
    - `enviar(nfse, homologacao=False)`
    - `gerarDPS(nfse, homologacao=False)`: gera, assina e valida sem enviar
    - `consultar(chaveAcesso, homologacao=False)`
    - `consultarDps(idDps, homologacao=False)`
    - `cancelar(...)` e consulta de eventos (a implementar)
- `serializacao.py` (implementado): gera o XML da DPS. Veja "Serialização da DPS".
- `assinatura.py` (implementado): assina a DPS. Veja "Assinatura da DPS".
- `validacao.py` (implementado): `Validacao(versao='1.01').validarDPS(dps)` valida a DPS com o XSD; os erros ficam em `erros`.
- `comunicacao.py` (implementado): requisições JSON por HTTPS com o certificado A1, um método por endpoint (`enviarDPS`, `consultarNFSe`, `consultarDPS`, `existeDPS`, `registrarEvento`, `consultarEvento`). Devolve o `requests.Response` sem interpretar.
- `resposta.py` (implementado): interpreta as respostas, descompacta os XMLs e levanta `ErroSefin` nos dois formatos de erro da API.
- `flags.py` (implementado): URLs dos ambientes, namespace, versões e códigos usados na DPS.

## Serialização da DPS

```python
from pynfe.processamento.nfse.nfse_nacional import serializacao

dps = serializacao.Serializacao().gerar(nfse, homologacao=False)  # etree._Element, sem assinatura
```

Gera a DPS no leiaute 1.01 a partir de um `NotaFiscalServico`. Por enquanto cobre o núcleo da DPS: identificação, prestador, tomador, serviço, valores, ISSQN, retenções federais e o grupo básico de IBS/CBS. Ainda não cobre substituição de NFS-e, intermediário, comércio exterior, obra, evento, deduções/reduções, benefício municipal, PIS/COFINS e o detalhamento de IBS/CBS.

As regras de negócio vêm da planilha `nfse-v1-01-20260209.xlsx` (aba `RN DPS_NFS-e`). As que podem ser verificadas sem consultar os cadastros da Sefin levantam `ErroRegraNegocio`, com o código da regra no início da mensagem, antes de gerar o XML. Veja "Regras de negócio verificadas localmente".

### Identificação

| Campo | Origem |
|---|---|
| `infDPS/@Id` | `"DPS"` + `cLocEmi` (7) + tipo de inscrição (1 = CPF, 2 = CNPJ) + CNPJ/CPF do emitente (14, zeros à esquerda) + `serie` (5) + `nDPS` (15) |
| `tpAmb` | parâmetro `homologacao` (1 produção, 2 homologação) |
| `dhEmi` | `data_emissao`. Sem fuso (`tzinfo`), usa `-03:00` |
| `verAplic` | `"PyNFe"` |
| `serie` | `serie`. **Só números**, de 1 a 49999 (faixa de aplicativo próprio, E0010) |
| `nDPS` | `identificador`, sem zeros à esquerda |
| `dCompet` | `data_competencia`; se não houver, a data de `data_emissao`. Não pode ser posterior à emissão (E0015) |
| `tpEmit` | `tipo_emitente` (padrão 1, prestador). A Sefin só aceita 1 nesta versão (E9996) |
| `cLocEmi` | `emitente.endereco_cod_municipio` |

### Prestador (`prest`)

| Campo | Origem |
|---|---|
| `CNPJ` / `CPF` | `emitente.cnpj` (11 dígitos = CPF) |
| `IM` | `emitente.inscricao_municipal`, se houver e se `prestador_informar_im` não for `False`. A IM deve ir se, e somente se, a empresa tiver registro no CNC do município emissor (E0116/E0120) |
| `xNome`, `end` | só quando `tipo_emitente` não é 1: com o prestador como emitente, vêm do cadastro nacional |
| `fone` | `emitente.endereco_telefone`, só os números |
| `email` | `emitente.email`, se houver |
| `regTrib/opSimpNac` | `op_simples_nacional`; se não houver, `simples == 1` vira 3 (ME/EPP) e os demais 1 (não optante). MEI (2) só pelo atributo |
| `regTrib/regApTribSN` | só para ME/EPP (`opSimpNac` 3), obrigatório nesse caso (E0162/E0166). `regime_apuracao_sn`, padrão 1: tributos federais e ISSQN pelo SN; 2: federais pelo SN e ISSQN pela legislação municipal; 3: ambos fora do SN |
| `regTrib/regEspTrib` | `regime_especial` (padrão 0). Deve ser 0 para MEI, para ME/EPP com `regApTribSN` 1 e para operação não tributável (E0172/E0174/E0175) |

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
| `trib/tribMun/tpRetISSQN` | `servico.tipo_retencao_issqn`; se não houver, `iss_retido == 1` vira 2 (retido pelo tomador) e os demais 1 (não retido). Sem retenção para MEI, regime especial ou operação não tributável (E0580/E0583/E0588) |
| `trib/tribMun/pAliq` | `servico.aliquota`, só quando as regras exigem (veja abaixo). Máximo 5% (E0595) |
| `trib/tribFed` | `vRetCP` = `valor_inss`, `vRetIRRF` = `valor_ir`, `vRetCSLL` = `valor_csll`, quando maiores que zero e menores que o valor do serviço. Não permitido para emitente CPF ou MEI (E0675/E0676) |
| `trib/totTrib` | veja "Total aproximado dos tributos" abaixo |

### IBS/CBS (`IBSCBS`)

Só é gerado quando `IBSCBS_cIndOp` está preenchido. Usa os mesmos atributos do São Paulo: `IBSCBS_finNFSe`, `IBSCBS_indFinal`, `IBSCBS_cIndOp`, `IBSCBS_tpOper`, `IBSCBS_indDest` e `IBSCBS_cClassTrib`, mais `IBSCBS_CST` (3 dígitos), obrigatório no leiaute nacional.

### Alíquota do ISSQN (`pAliq`)

Quando o município de incidência tem convênio ativo no Sistema Nacional, a alíquota vem da parametrização do município. A regra resultante (E0595 a E0640):

| Situação | `pAliq` |
|---|---|
| MEI, regime especial ou operação não tributável | não informado |
| ME/EPP com `regApTribSN` 1 e ISSQN retido | obrigatório |
| ME/EPP com `regApTribSN` 1 e ISSQN não retido | não informado |
| Demais casos, município de incidência conveniado | não informado |
| Demais casos, município de incidência não conveniado | obrigatório |

O atributo `municipio_incidencia_conveniado` (padrão `True`) indica se o convênio do município de incidência está ativo. Quando `pAliq` não deve ser informado, `servico.aliquota` é ignorado; quando é obrigatório e está vazio, a serialização falha.

### Total aproximado dos tributos (`totTrib`)

Regras E0710, E0712 e E0713:

| Opção no Simples | Aceito |
|---|---|
| Não optante | `vTotTrib` ou `pTotTrib` |
| MEI | `vTotTrib`, `pTotTrib` ou `indTotTrib` = 0 |
| ME/EPP | `vTotTrib`, `pTotTrib` ou `pTotTribSN` |

A serialização usa, nesta ordem: `valor_tributos_aproximados` (tupla federal, estadual, municipal) → `vTotTrib`; `percentual_tributos_aproximados` (tupla) → `pTotTrib`; `percentual_tributos_sn` (ME/EPP) → `pTotTribSN`; para MEI sem nada informado, `indTotTrib` = 0. Sem informação para ME/EPP ou não optante, a serialização falha.

### Regras de negócio verificadas localmente

Levantam `ErroRegraNegocio` antes de gerar o XML:

| Código | Regra |
|---|---|
| E0010 | série fora da faixa 1 a 49999 |
| E0015 | data de competência posterior à emissão |
| E9996 | emitente diferente do prestador |
| E0172, E0174, E0175 | regime especial de tributação não permitido |
| E0204, E0235, E0237 | tomador ou endereço do tomador ausente quando obrigatório |
| E0580, E0583, E0588 | retenção do ISSQN não permitida |
| E0595, E0619 e correlatas | alíquota acima de 5% ou ausente quando obrigatória |
| E0675, E0676, E0699 a E0701 | tributos federais não permitidos ou fora dos limites |
| E0712, E0713 | total aproximado dos tributos ausente |
| E0322 | NBS ausente com IBS/CBS informado |

Regras que dependem dos cadastros da Sefin (CNPJ, Simples Nacional, CNC, convênio, parametrização do município) só são verificadas no envio.

### Atributos novos

Como em São Paulo, os campos que não existem nas entidades são atributos extras do `NotaFiscalServico` e do `Servico`, sem alterar `pynfe/entidades`:

- `NotaFiscalServico`: `data_competencia`, `tipo_emitente`, `op_simples_nacional`, `regime_apuracao_sn`, `prestador_informar_im`, `municipio_incidencia_conveniado`, `percentual_tributos_sn`, `valor_tributos_aproximados`, `percentual_tributos_aproximados`, `IBSCBS_CST`.
- `Servico`: `codigo_tributacao_nacional`, `codigo_tributacao_municipal_nacional`, `tributacao_issqn`, `tipo_retencao_issqn`.

## Assinatura da DPS

A Sefin rejeita prefixos de namespace na área de dados (regra E1228 da aba `RN_RECEPCAO_DPS`), por isso a `Signature` usa o namespace padrão, sem `ds:`.

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

## Uso

```python
from pynfe.processamento.nfse import autorizador
from pynfe.processamento.nfse.nfse_nacional.resposta import ErroSefin
from pynfe.processamento.nfse.nfse_nacional.serializacao import ErroRegraNegocio
from pynfe.processamento.nfse.nfse_nacional.servicos import ErroComunicacao

servicos = autorizador.get(cidade, certificado, senha, nfse_nacional=True)
try:
    r = servicos.enviar(nfse, homologacao=True)
except ErroRegraNegocio as e:   # dados violam uma regra verificada localmente; nada foi enviado
    ...
except ErroSefin as e:          # a Sefin recusou: e.status, e.codigos, e.erros, e.idDps
    ...
except ErroComunicacao as e:    # falha de rede e não há NFS-e gerada: pode reenviar a mesma nota
    ...

r["chaveAcesso"]   # chave de acesso da NFS-e (50 dígitos)
r["idDps"]         # Id da DPS
r["nfseXml"]       # XML da NFS-e gerada pela Sefin (str)
r["alertas"]       # lista de {codigo, descricao, complemento}
```

`Servicos(certificado, senha, timeout=60, verificar_ssl=True)`: `timeout` em segundos para cada requisição; `verificar_ssl` é repassado ao `verify` do requests (pode ser o caminho de um arquivo de cadeia de certificados, se o servidor da Sefin usar uma cadeia que o certifi não reconhece).

O mesmo `homologacao` define o `tpAmb` da DPS e a URL, que precisam coincidir (regra E0006).

## Fluxo de `enviar`

1. Serializa a DPS em XML. Regras de negócio violadas levantam `ErroRegraNegocio`.
2. Assina o XML com o certificado A1 (XMLDSIG).
3. Valida o XML com o XSD. Se for inválido, levanta `Exception` com a lista de erros e não envia.
4. Compacta em GZip, codifica em base64 e envia em `POST /nfse`.
5. Interpreta a resposta: no sucesso (201) devolve o dicionário acima; em qualquer outro caso levanta `ErroSefin`.

O certificado é gravado em arquivos temporários a cada requisição, como na comunicação de São Paulo, e excluído logo depois.

### Falha de rede no envio

Se o `POST /nfse` falhar por timeout ou queda de conexão, não há como saber se a NFS-e foi gerada. O `enviar` consulta então `GET /dps/{id}`:

- 200: a NFS-e foi gerada. Busca a NFS-e pela chave e devolve o resultado normalmente, com `recuperada = True`.
- 404, ou nova falha de rede: levanta `ErroComunicacao`.

Depois de um `ErroComunicacao` é seguro reenviar a mesma nota (mesma série e número): a Sefin recusa uma DPS com série, número, município e CNPJ/CPF já usados em uma NFS-e (regra E0014), então o reenvio não gera nota em duplicidade. Uma nota com outro número, por outro lado, geraria outra NFS-e.

## Seleção do serviço

`autorizador.get` recebe o parâmetro `nfse_nacional` (padrão `False`):

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

- Confirmar o algoritmo de assinatura aceito (RSA-SHA1 ou RSA-SHA256): a planilha de regras não trata disso.
- Confirmar se o município emissor (`cLocEmi`) tem convênio ativo no Sistema Nacional e permite os emissores públicos (E0037/E0038/E0039); sem isso a Sefin rejeita a DPS.
- Confirmar, para cada empresa, se ela tem registro no CNC do município emissor, para decidir `prestador_informar_im` (E0116/E0120).
- Significado dos tipos de evento.
- Incluir os XSDs no `package_data` do `setup.py` (hoje só `data/**/*.txt` é incluído).

# Testes

Ficam em `tests/processamento/nfse/nfse_nacional/`. Para rodar, a partir da raiz do projeto:

```
python -m tests.processamento.nfse.nfse_nacional.suite
```

- `compactador.py`: testes do `Compactador`.
- `assinatura.py`: testes da assinatura, com verificação independente do libxml2.
- `servicos.py`: testes da comunicação com o `requests` simulado (envio, rejeição, resposta não JSON, recuperação após falha de rede, consultas e autorizador). Não acessam a Sefin.
- `serializacao.py`: testes da serialização da DPS, incluindo a validação com o XSD 1.01. A função `get_nfse()` monta uma NFS-e de exemplo.
