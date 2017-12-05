"""
a template for any strategy
"""
import time
from observer import *
from hydra_quote_manager import HydraQuoteManager
from order_factory import OrderFactory
import threading
from order import *


class Strategy(object):

    def __init__(self, quoteManger, executionManager):
        self.qm = quoteManger
        self.em = executionManager
        self.of = OrderFactory()
        self.quotes = {}
        self.quotes_lock = threading.Lock()
        self.open_orders = {}
        self.open_orders_lock = threading.Lock()
        self.closed_orders = {}
        self.closed_orders_lock = threading.Lock()

        # ----- observers -----
        self.bidObserver = Strategy.BidObserver(self)
        self.askObserver = Strategy.AskObserver(self)
        self.lastObserver = Strategy.LastObserver(self)
        self.orderStatusObserver = Strategy.OrderStatusObserver(self)
        self.timer_thread = 0
        self.run = False

    def start(self):
        if self.run: return
        self.run = True

        self.timer_thread = threading.Thread(target=self.on_second)
        self.timer_thread.start()

    def stop(self):
        self.run = False
        with self.quotes_lock:
            for key, val in self.quotes.iteritems():
                self.qm.stop_quote_stream(val.symbol)

        with self.open_orders_lock:
            for key, val in self.open_orders.iteritems():
                self.em.cancel_order(val)

        if self.timer_thread:
            self.timer_thread.join()

        i = 0
        while len(self.open_orders) > 0:
            if i == 5: break
            time.sleep(1)
            i += 1

    def add_quote(self, symbol):
        if symbol in self.quotes: return
        q = self.qm.start_quote_stream(symbol)

        with self.quotes_lock:
            self.quotes[symbol] = q

        q.askNotifier.addObserver(self.askObserver)
        q.bidNotifier.addObserver(self.bidObserver)
        q.lastNotifier.addObserver(self.lastObserver)

    def on_ask(self, quote):
        pass

    def on_bid(self, quote):
        pass

    def on_last(self, quote):
        pass

    def on_order_status(self, ord):
        if ord.status == order_status_type.canceled:
            with self.open_orders_lock:
                o = self.open_orders[ord.parent_id]
                if o != None:
                    self.closed_orders[o.parent_id] = 0
                    del self.open_orders[ord.parent_id]

    def place_order(self, qty, symbol, price = 0, account = '', type = 'lmt'):
        o = None
        if type == 'lmt':
            o = self.of.generate_limit_order(qty, symbol, price, account)

        if not o: return
        with self.open_orders_lock:
            self.open_orders[o.parent_id] = o

        o.statusChangeNotifier.addObserver(self.orderStatusObserver)
        self.em.send_order(o)

    def on_second(self):
        while 1:
            #on second code
            if len(self.open_orders) == 0:
                bid = self.quotes['SPY'].get_bid()

                if bid != None:
                    self.place_order(100,'SPY', bid - 1, 'DEMOX1')

            else:
                with self.open_orders_lock:
                    for key, val in self.open_orders.iteritems():
                        self.em.cancel_order(val)

            # on second code
            if not self.run:
                break
            time.sleep(1)

    class AskObserver(Observer):
        def __init__(self, outer):
            self.outer = outer

        def update(self, arg):
            self.outer.on_ask(arg)

    class BidObserver(Observer):
        def __init__(self, outer):
            self.outer = outer

        def update(self, arg):
            self.outer.on_bid(arg)

    class LastObserver(Observer):
        def __init__(self, outer):
            self.outer = outer

        def update(self, arg):
            self.outer.on_last(arg)

    class OrderStatusObserver(Observer):
        def __init__(self, outer):
            self.outer = outer

        def update(self, arg):
            self.outer.on_order_status(arg)

