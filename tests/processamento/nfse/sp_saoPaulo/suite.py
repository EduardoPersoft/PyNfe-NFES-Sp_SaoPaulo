import unittest

from tests.processamento.nfse.sp_saoPaulo import assinaturaRPS
from tests.processamento.nfse.sp_saoPaulo import comunicacao
from tests.processamento.nfse.sp_saoPaulo import serializacao
from tests.processamento.nfse.sp_saoPaulo import validacao
from tests.processamento.nfse.sp_saoPaulo import autorizador
from tests.processamento.nfse.sp_saoPaulo import servicos
from tests.processamento.nfse.sp_saoPaulo import retorno

def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(assinaturaRPS))
    suite.addTests(loader.loadTestsFromModule(comunicacao))
    suite.addTests(loader.loadTestsFromModule(serializacao))
    suite.addTests(loader.loadTestsFromModule(validacao))
    suite.addTests(loader.loadTestsFromModule(autorizador))
    suite.addTests(loader.loadTestsFromModule(servicos))
    suite.addTests(loader.loadTestsFromModule(retorno))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite())
