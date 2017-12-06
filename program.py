import time
from strategy import Strategy
from hydra_quote_manager import HydraQuoteManager
from hydra_execution_manager import HydraExecutionManager

qm = HydraQuoteManager()
em = HydraExecutionManager()

s = Strategy(qm,em)
s.add_quote('SPY')
time.sleep(1)
s.start()
time.sleep(5)
s.stop()


qm.close_socket()
em.close_socket()
print 'done'
