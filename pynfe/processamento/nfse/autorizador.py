def get(cidade, certificado, senha, nfse_nacional=False, timeout=60):
    """timeout (segundos por requisição) só vale para a NFS-e Nacional."""

    if nfse_nacional:
        from pynfe.processamento.nfse.nfse_nacional import servicos as s_nfse_nacional
        return s_nfse_nacional.Servicos(certificado, senha, timeout=timeout)

    if cidade=='3550308':
        from pynfe.processamento.nfse.sp_saoPaulo import servicos as s_sp_saoPaulo
        return s_sp_saoPaulo.Servicos(certificado, senha)

    raise Exception("Cidade não implementada!")
