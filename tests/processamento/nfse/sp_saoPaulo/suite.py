import unittest

from tests.processamento.nfse.sp_saoPaulo import assinaturaRPS
from tests.processamento.nfse.sp_saoPaulo import comunicacao
from tests.processamento.nfse.sp_saoPaulo import serializacao
from tests.processamento.nfse.sp_saoPaulo import validacao

def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(assinaturaRPS))
    suite.addTests(loader.loadTestsFromModule(comunicacao))
    suite.addTests(loader.loadTestsFromModule(serializacao))
    suite.addTests(loader.loadTestsFromModule(validacao))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite())
