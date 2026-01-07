def get(cidade, certificado, senha):

    if cidade=='3550308':
        from pynfe.processamento.nfse.sp_saoPaulo import servicos as s_sp_saoPaulo
        return s_sp_saoPaulo.Servicos(certificado, senha)

    raise Exception("Cidade não implementada!")
