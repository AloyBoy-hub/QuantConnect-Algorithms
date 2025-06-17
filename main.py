# region imports
from AlgorithmImports import *
# endregion

class CoveredWriteAlgorithm(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2020,1,1)
        self.set_cash(100000)
        
        equity = self.add_equity("IBM", Resolution.DAILY)
        self.equity_symbol = equity.symbol
        option = self.add_option(self.equity_symbol, Resolution.DAILY)
        self.option_symbol = option.symbol

        option.set_filter(lambda universe: universe.standards_only().strikes(-15, 15).expiration(0,30))
        
        self.set_benchmark(self.equity_symbol)

    def on_data(self, data: Slice): 
        #check to see if there are open options
        if any(
            security.invested and security.symbol.id.security_type == SecurityType.OPTION
            for security in self.securities.values()
        ):
            return
        
        #buying shares
        shares_held = self.portfolio[self.equity_symbol].quantity
        if shares_held != 1000:
            purchase = 1000 - shares_held
            self.market_order(self.equity_symbol, purchase)
        
        #choosing which option to buy
        chain = data.option_chains.get(self.option_symbol)
        if chain:
            call = [x for x in chain if x.right == OptionRight.CALL]
            call = sorted(call, key = lambda x: x.strike, reverse=True)
            self.market_order(call[0].symbol, -10)

    def on_order_event(self, order_event: OrderEvent) -> None:
        # Only proceed if the order was filled
        if order_event.status != OrderStatus.FILLED:
            return

        security = self.securities[order_event.symbol]
        security_type = order_event.symbol.id.security_type
        direction = order_event.direction

        # Handle share purchases
        if security_type == SecurityType.EQUITY and direction == OrderDirection.BUY:
            self.log(f"Bought {order_event.fill_quantity} shares of {security.symbol}")

        # Handle call option sales
        elif (
            security_type == SecurityType.OPTION
            and direction == OrderDirection.SELL
            and order_event.symbol.id.option_right == OptionRight.CALL
        ):
            strike = order_event.symbol.id.strike_price
            expiry_date = order_event.symbol.id.date
            expiry_str = expiry_date.strftime("%Y-%m-%d")
            self.log(f"Sold {order_event.fill_quantity} call option(s) of {security.symbol} (strike={strike}, expiry={expiry_str})")

