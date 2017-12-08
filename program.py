import time
from strategy import Strategy
from HydraQuoteManager import HydraQuoteManager
from HydraOrderManager import HydraOrderManager

qm = HydraQuoteManager()
em = HydraOrderManager()

s = Strategy(qm,em)
s.add_quote('SPY')
time.sleep(1)
s.start()
time.sleep(5)
s.stop()
qm.stop_quote_stream('SPY')


qm.close_socket()
em.close_socket()
print 'done'
