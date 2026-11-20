import unittest

from tests.processamento.nfse.nfse_nacional import compactador
from tests.processamento.nfse.nfse_nacional import serializacao
from tests.processamento.nfse.nfse_nacional import assinatura

def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(compactador))
    suite.addTests(loader.loadTestsFromModule(serializacao))
    suite.addTests(loader.loadTestsFromModule(assinatura))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite())
