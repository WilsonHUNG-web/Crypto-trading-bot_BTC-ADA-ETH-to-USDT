class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            'Binance': {
                'pairs': ['BTC-USDT'],
            },
        }
        self.period = 15 * 60 #15 mins bar
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = None
        self.close_price_trace = np.array([])
        self.ma_long = 15
        self.ma_short = 5
        self.UP = 1
        self.DOWN = 2
        self.RSI = -1
        self.stop_flag = False
        self.stage1 = False
        self.stage2 = False
        self.stage3 = False


    def on_order_state_change(self,  order):
        Log("on order state change message: " + str(order) + " order price: " + str(order["price"]))

    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
        if np.isnan(s_ma) or np.isnan(l_ma):
            return None
        if s_ma > l_ma:
            return self.UP
        return self.DOWN

    def get_rsi(self):
        self.RSI = talib.RSI(self.close_price_trace)
        return self.RSI


    # called every self.period
    def trade(self, information):
        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        target_currency = pair.split('-')[0]  #BTC
        base_currency = pair.split('-')[1]  #USDT
        base_currency_amount = self['assets'][exchange][base_currency] 
        target_currency_amount = self['assets'][exchange][target_currency] 
        # add latest price into trace
        close_price = information['candles'][exchange][pair][0]['close']
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-self.ma_long:]
        # calculate current ma cross status
        cur_cross = self.get_current_ma_cross()
        rsi = self.get_rsi()
        r = rsi[-1]
        #Log('Capital = ' + str(base_currency_amount + target_currency_amount*close_price) + 'USDT')
        profit = ((base_currency_amount + target_currency_amount*close_price) / 100000)*100-100
        #Log('RSI='+str(r))
        #Log('Profit=  ' +str(profit) )
        #stop_flag = False
        if profit > 1:
            self.stop_flag = True
            self.stage1 = True
            #Log('current profit = ' + str(profit))
        if profit > 2:
            self.stage2 = True
        if profit > 3:
            self.stage3 = True

        if cur_cross is None:
            return []
        if self.last_cross_status is None:
            self.last_cross_status = cur_cross
            return []

        rsibuy = 30 
        rsisell = 80

        if profit > 0:
            rsibuy = 30 - profit
            rsisell = 80 + profit
        #if self.stage1 == True:
        #    rsibuy =  25
        #    rsisell = 85
        
        #if self.stage2 == True:
        #    rsibuy =  20
        #    rsisell = 90           

        # r<30, buy 0.1 BTC
        #if r<rsibuy and self.stop_flag==False:
        if r<rsibuy:
        #if self.last_type == 'sell' and r<30:
            Log('buy RSI='+str(r))
            #Log('buying 0.1 unit of ' + str(target_currency))
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': 0.1,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        # rsi>80, sell 0.1BTC
        #elif self.last_type == 'buy' and r>80:
        #elif r>rsisell or self.stop_flag==True:
        elif r>80 and target_currency_amount>0:
            Log('sell RSI='+str(r))
            #Log('assets before selling: ' + str(self['assets'][exchange][base_currency]))
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    #'amount': -0.1,
                    'amount': -target_currency_amount*0.1,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        self.last_cross_status = cur_cross
        return []
