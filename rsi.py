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
                'pairs': ['ADA-USDT'],
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
        self.RSI_mid = -1
        self.RSI_long = -1
        self.RSI_long_long = -1
        self.stop_flag = False
        self.pre_RSI =-1
        self.prepre_RSI = -1
        self.init_amount = 0
        self.initialized = False
        self.profit = 0
        self.portions = 20.0

        self.RSI_buy_signal = 0
        self.RSI_sell_signal = 0

        self.unittrade_base = 0

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
        RSI = talib.RSI(self.close_price_trace, timeperiod = 2)
        self.RSI = RSI[-1]
        #return self.RSI

    def get_rsi_mid(self):
        RSI_mid = talib.RSI(self.close_price_trace, timeperiod = 6)
        self.RSI_mid = RSI_mid [-1]
        #return self.RSI_mid   

    def get_rsi_long(self):
        RSI_long = talib.RSI(self.close_price_trace, timeperiod = 10)
        self.RSI_long = RSI_long[-1]
        #return self.RSI_long

   #def get_rsi_long_long(self):
   #     RSI_long_long = talib.RSI(self.close_price_trace, timeperiod = 14)
    #    self.get_rsi_long_long = RSI_long_long[-1]
        #return self.RSI_long

    def initialization(self, amount):
        self.init_amount = amount
        self.unittrade_base = self.init_amount/self.portions
        self.initialized = True


    # called every self.period
    def trade(self, information):
        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        target_currency = pair.split('-')[0]  #ETH
        base_currency = pair.split('-')[1]  #USDT
        base_currency_amount = self['assets'][exchange][base_currency] 
        if not self.initialized:
            self.initialization(base_currency_amount)

        target_currency_amount = self['assets'][exchange][target_currency] 
        # add latest price into trace
        close_price = information['candles'][exchange][pair][0]['close']
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-self.ma_long:]
        # calculate current ma cross status
        #cur_cross = self.get_current_ma_cross()
        #Log('RSI='+str( self.RSI ))
        #self.RSI = (self.get_rsi())[-1]
        #self.RSI_mid = (self.get_rsi_mid())[-1]
        #self.RSI_long = (self.get_rsi_long())[-1]
        self.get_rsi()
        self.get_rsi_mid()
        self.get_rsi_long()
        #self.get_rsi_long_long()

        cur_cross = self.get_current_ma_cross()
        Log('last_cross: ' + str(self.last_cross_status))
        Log('cur_cross: ' + str(cur_cross))

        #Log('RSI='+str( self.RSI )+' pre-RSI='+str( self.pre_RSI )+' prepre-RSI='+str( self.prepre_RSI ))

        Log('Capital = ' + str(base_currency_amount + target_currency_amount*close_price) + 'USDT')
        self.profit = ((base_currency_amount + target_currency_amount*close_price) / self.init_amount) -1.0
        
        #Log('Profit=  ' +str(profit) )
        #stop_flag = False
        if self.profit < -0.15:
            self.stop_flag = True
            Log('Current profit = ' + str(self.profit) + '. stop trade if profit < -0.1' )
        if self.RSI_mid<20 and self.RSI_mid>0 and self.RSI < self.pre_RSI:
            self.stop_flag = False #back to market
            
        if cur_cross is None:
            return []
        if self.last_cross_status is None:
            self.last_cross_status = cur_cross
            return []
        #real = talib.AVGPRICE()
        #Log('real='+str(real))

        # r<30, buy 0.1 BTC
        #if r<20 and self.stop_flag==False:
        
        #if (self.RSI <20 and self.pre_RSI<20 and self.prepre_RSI <20)\
        #and (self.RSI >0 and self.pre_RSI>0  and self.prepre_RSI>0 )\
        #and self.stop_flag ==False:

        if (self.RSI <20 and self.RSI_mid<20)\
        and (self.RSI >0 and self.RSI_mid>0  )\
        and self.stop_flag ==False:
        #and cur_cross == self.UP and self.last_cross_status == self.DOWN:

            Log('case-1')
            self.pre_RSI = self.RSI
            self.prepre_RSI = self.pre_RSI
        #if self.last_type == 'sell' and r<30:
            #Log('RSI='+str(r))
            Log('buying '+ str(self.unittrade_base / close_price) +' unit of ' + str(target_currency))
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': self.unittrade_base / close_price,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
            self.RSI_buy_signal  =0
        # rsi>80, sell BTC
        #elif (self.RSI >80 and self.pre_RSI>80 and self.prepre_RSI >80) and self.stop_flag ==False:
        #elif (self.RSI >80 and self.pre_RSI>80 ) and self.stop_flag ==False:
        #and cur_cross == self.DOWN and self.last_cross_status == self.UP:
        elif (self.RSI >80 and self.RSI_mid>80 ) and self.stop_flag ==False:
        
            Log('case-2')
            self.pre_RSI = self.RSI
            self.prepre_RSI = self.pre_RSI
            #Log('assets before selling: ' + str(self['assets'][exchange][base_currency]))
            Log('selling '+ str(self.unittrade_base / close_price) +' unit of ' + str(target_currency))
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': -self.unittrade_base / close_price,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif (self.RSI > self.pre_RSI and self.pre_RSI>80) and self.stop_flag ==False:
        
            Log('case - 3 increaseing RSI, sell all')
            self.pre_RSI = self.RSI
            self.prepre_RSI = self.pre_RSI
            #Log('assets before selling: ' + str(self['assets'][exchange][base_currency]))
            Log('selling '+ str(self.unittrade_base / close_price) +' unit of ' + str(target_currency))
            self.last_type = 'sellall'
            self.last_cross_status = cur_cross
            self.stop_flag = True
            return [
                {
                    'exchange': exchange,
                    'amount': -target_currency_amount,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]

        elif self.stop_flag == True and self.last_type != 'sellall':
            Log('case-4: stopflag')
            self.pre_RSI = self.RSI
            self.prepre_RSI = self.pre_RSI
            self.last_cross_status = cur_cross
            Log('selling all: '+ str(self.unittrade_base / close_price) +' unit of ' + str(target_currency))
            self.last_type = 'sellall'
            return [
                {
                    'exchange': exchange,
                    'amount': -target_currency_amount,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        else:
            Log('else')
            self.pre_RSI = self.RSI
            self.prepre_RSI = self.pre_RSI
            self.last_cross_status = cur_cross
            return []
