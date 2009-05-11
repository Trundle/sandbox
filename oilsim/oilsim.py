#!/usr/bin/env python

from __future__ import division, with_statement

from collections import defaultdict

import random
import sys

""" price of a new pump """
PUMP_BUY_PRICE = 1000
""" value of an pump """
PUMP_SELL_PRICE = PUMP_BUY_PRICE
""" liters of oil produced by one pump / per month """
PUMP_OUTPUT = 100
""" total amount of rounds to play (note: 1 round = 1 month) """
ROUNDS = 1000*12
""" the cost of operationg a pump per month """
PUMP_MAINTENANCE_COST = 100

def _flatten(lol):
    for i in lol:
        if isinstance(i, (tuple, list)):
            for t in _flatten(i):
                yield t
        else:
            yield i

def flatten(lol):
    """ Flattens tuples and lists. """
    return list(_flatten(lol)) if isinstance(lol, list) else tuple(_flatten(lol))

class PayoffMatrix(object):
    def __init__(self, market, player1, player2):
        self.player1 = player1
        self.player2 = player2

        self.pm = {'BB': 0, 'B0': 0, 'BS': 0,
                   '0B': 0, '00': 0, '0S': 0,
                   'SB': 0, 'S0': 0, 'SS': 0}

        supply = market.supply
        demand = market.demand

        # revenue, oil sold, potential
        p1r, p1s, p1p, p2r, p2s, p2p = market.revenue(player1.pumps, player2.pumps)
        self.pm['00'] = (0, 0)
        
        p1rt, p1s, p1p, p2rt, ps2, p2p = market.revenue(player1.pumps - 1, player2.pumps - 1)
        self.pm['SS'] = (p1rt - p1r, p2rt - p2r)

        p1rt, p1s, p1p, p2rt, ps2, p2p = market.revenue(player1.pumps - 1, player2.pumps)
        self.pm['S0'] = (p1rt - p1r, p2rt - p2r)
        
        p1rt, p1s, p1p, p2rt, ps2, p2p = market.revenue(player1.pumps - 1, player2.pumps + 1)
        self.pm['SB'] = (p1rt - p1r, p2rt - p2r)

        p1rt, p1s, p1p, p2rt, ps2, p2p = market.revenue(player1.pumps, player2.pumps - 1)
        self.pm['0S'] = (p1rt - p1r, p2rt - p2r)

        p1rt, p1s, p1p, p2rt, ps2, p2p = market.revenue(player1.pumps, player2.pumps + 1)
        self.pm['0B'] = (p1rt - p1r, p2rt - p2r)

        p1rt, p1s, p1p, p2rt, ps2, p2p = market.revenue(player1.pumps + 1, player2.pumps - 1)
        self.pm['BS'] = (p1rt - p1r, p2rt - p2r)

        p1rt, p1s, p1p, p2rt, ps2, p2p = market.revenue(player1.pumps + 1, player2.pumps)
        self.pm['B0'] = (p1rt - p1r, p2rt - p2r)
        
        p1rt, p1s, p1p, p2rt, ps2, p2p = market.revenue(player1.pumps + 1, player2.pumps + 1)
        self.pm['BB'] = (p1rt - p1r, p2rt - p2r)

    def __str__(self):
        str = "   |                      B |                      0 |                      S \n" \
            " B | %10.2f, %10.2f | %10.2f, %10.2f | %10.2f, %10.2f\n" \
            " 0 | %10.2f, %10.2f | %10.2f, %10.2f | %10.2f, %10.2f\n" \
            " S | %10.2f, %10.2f | %10.2f, %10.2f | %10.2f, %10.2f\n" \
            % flatten(self.pm[k] for k in ('BB', 'B0', 'BS', '0B', '00', '0S', 'SB', 'S0', 'SS'))

        return str

    def getdata(self, player, act):
        if player.name == self.player1.name:
            return (self.pm[act + 'B'], self.pm[act + '0'], self.pm[act + 'S'])
        else:
            return map(list, map(reversed, (self.pm['B' + act], self.pm['0' + act], self.pm['S' + act])))

class OilProducer(object):
    def __init__(self, initialpumps, initialmoney, name=None):
        self.pumps = initialpumps
        self.money = initialmoney
        self.oldmoney = initialmoney
        self.dmoney = 0
        if name is None:
            self.name = 'unnamed oil producer'
        else:
            self.name = name
        self.dpumps = 0

    def buy_pump(self, market):
        print '%s buys a pump.' % self.name
        if self.money >= market.pump_buy_price:
            self.dpumps += 1
            self.money -= market.pump_buy_price
            return True
        else:
            return False

    def sell_pump(self, market):
        print '%s sells a pump.' % self.name
        if self.pumps > 0:
            self.dpumps -= 1
            self.money += market.pump_sell_price
            return True
        else:
            return False

    def begin_round(self):
        self.pumps += self.dpumps
        self.dpumps = 0
        self.oldmoney = self.money

    def end_round(self, revenue):
        self.money += revenue
        self.dmoney = self.money - self.oldmoney

    def __str__(self):
        return self.name

class Strategy(object):
    def __init__(self, producer):
        self.producer = producer

    def begin_round(self):
        self.producer.begin_round()

    def end_round(self, revenue, output):
        self.producer.end_round(revenue)
        return PlayerStat(self.producer.name, self.producer.money,
                          self.producer.dmoney, self.producer.pumps,
                          output)

    name = property(lambda self: self.producer.name)
    pumps = property(lambda self: self.producer.pumps)
    money = property(lambda self: self.producer.money)

class RandomStrategy(Strategy):
    def __init__(self, producer):
        Strategy.__init__(self, producer)

    def decide(self, pm, market):
        i = random.randint(0,2)
        if i == 1 and self.producer.pumps > 1:
            return 'S'
        elif i == 2:
            return 'B'
        return '0'

class TakeBestStrategy(Strategy):
    def __init__(self, producer):
        Strategy.__init__(self, producer)

    def decide(self, pm, market):
        def max1(l):
            return max(x[0] for x in l)

        b = max1(pm.getdata(self, 'B'))
        z = max1(pm.getdata(self, '0'))
        s = max1(pm.getdata(self, 'S'))
        m = max(b, z, s)
        if m == b:
            return 'B'
        elif m == s:
            return 'S'
        return '0'

class SimpleOilPriceModell(object):
    def __init__(self, factor):
        self.factor = factor

    def update(self, round, demand, act_supply, supply):
        self.demand = demand
        self.supply = supply

        try:
            self.price = self.factor * self.demand / self.supply
        except ZeroDivisionError:
            self.price = self.factor * self.demand / 10**-8

class ConstantDemandModell(object):
    def __init__(self, demand=200):
        self.demand = 200

    def update(self, *args):
        pass

class LinearDemandModell(object):
    def __init__(self, d=200, k=1/10):
        self.d = d
        self.k = k

    def update(self, round, *args):
        self.demand = self.k * round + self.d

class ConstantPumpModell(object):
    def __init__(self, buy_price, sell_price, maintenance_cost, output):
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.maintenance_cost = maintenance_cost
        self.output = output

    def update(self, *args):
        pass

class Market(object):
    def __init__(self, total_oil, oil_modell, pump_modell, demand_modell):
        self.total_oil = total_oil
        self.oil_modell = oil_modell
        self.pump_modell = pump_modell
        self.demand_modell = demand_modell
    
    def update(self, round, act_supply, supply):
        self.supply = supply
        self.demand_modell.update(round, act_supply, supply)
        self.oil_modell.update(round, self.demand, act_supply, supply)
        self.pump_modell.update(round, self.demand, act_supply, supply)
        self.total_oil -= act_supply

    demand = property(lambda self: self.demand_modell.demand)
    oil_price = property(lambda self: self.oil_modell.price)
    pump_buy_price = property(lambda self: self.pump_modell.buy_price)
    pump_sell_price = property(lambda self: self.pump_modell.sell_price)
    pump_output = property(lambda self: self.pump_modell.output)
    pump_maintenance_cost = property(lambda self: self.pump_modell.maintenance_cost)

    def revenue(self, pumpsp1, pumpsp2):
        """ Calculate revenues of player 1 and 2 based on their pumps. """

        if pumpsp1 + pumpsp2 == 0:
            return (0, 0, 0, 0, 0, 0)

        # calculate the relative sizes
        p1s = pumpsp1 / (pumpsp1 + pumpsp2)
        p2s = 1 - p1s
        
        # oil produced per player
        p1o = pumpsp1 * self.pump_output
        p2o = pumpsp2 * self.pump_output

        # amount of sold oil (total and per player)
        oilsold = min(p1o + p2o, self.demand)
        p1s = p1s * oilsold
        p2s = p2s * oilsold

        # revene of both players
        p1r = self.oil_price * p1s - self.pump_maintenance_cost * pumpsp1
        p2r = self.oil_price * p2s - self.pump_maintenance_cost * pumpsp2
        return (p1r, p1s, p1o, p2r, p2s, p2o)

class PlayerStat(object):
    def __init__(self, name, money, moneydiff, pumps, supply, potential=0):
        self.name = name
        self.money = money
        self.moneydiff = moneydiff
        self.pumps = pumps
        self.supply = supply
        self.potential = potential

    def __str__(self):
        return "\t%s:\n\t\tmoney:  %10.2f\n\t\tdmoney: %10.2f\n\t\tpumps:  %d\n\t\tsupply: %10.2f (potential: %10.2f)\n" \
            % (self.name, self.money, self.moneydiff, self.pumps, self.supply, self.potential)
        

class RoundStat(object):
    def __init__(self, round, price, demand, supply, potential, player_stats):
        self.round = round
        self.price = price
        self.demand = demand
        self.supply = supply
        self.potential = potential
        self.player_stats = player_stats

    def __str__(self):
        str_ = "round %d:\n\toil price:  %10.2f\n\toil demand: %10.2f\n\toil supply: %10.2f (potential: %10.2f)\n" \
                % (self.round, self.price, self.demand, self.supply, self.potential)
        for stat in self.player_stats:
            str_ += str(stat)

        return str_


def print_mat(n, m, f=sys.stdout):
      f.write("%s = %s;\n" % (n, str(m).replace('[', '{').replace(']', '}')))

def main():
    opm = SimpleOilPriceModell(100)
    pm = ConstantPumpModell(PUMP_BUY_PRICE, PUMP_SELL_PRICE, PUMP_MAINTENANCE_COST, PUMP_OUTPUT)
    market = Market(10000000, opm, pm, LinearDemandModell())
    producer1 = OilProducer(10, 10000, 'Player 1')
    producer2 = OilProducer(10, 10000, 'Player 2')
    player1 = TakeBestStrategy(producer1) # RandomStrategy(producer1)
    player2 = TakeBestStrategy(producer2) # RandomStrategy(producer2)
    market.update(0, 0, (player1.pumps + player2.pumps) * market.pump_output) # we need to start with some inital value

    rstats = defaultdict(list) 
    stats = {-1: RoundStat(-1, market.oil_price, market.demand, 0, 0,
                           (player1.end_round(0, 0), player2.end_round(0, 0)))}
    print stats[-1]

    for rnum in xrange(ROUNDS):
        print 'in round %d' % rnum
        
        pm = PayoffMatrix(market, player1, player2)
        print 'payoff matrix:'
        print str(pm)

        player1.begin_round()
        player2.begin_round()

        p1d = player1.decide(pm, market)
        p2d = player2.decide(pm, market)

        if p1d == 'B':
            player1.producer.buy_pump(market)
        elif p1d == 'S':
            player1.producer.sell_pump(market)
        
        if p2d == 'B':
            player2.producer.buy_pump(market)
        elif p2d == 'S':
            player2.producer.sell_pump(market)

        # revenue, oil sold, potential
        p1r, p1s, p1p, p2r, p2s, p2p = market.revenue(player1.pumps, player2.pumps)
        stat = [player1.end_round(p1r, p1s), player2.end_round(p2r, p2s)]
        stat[0].potential = p1p
        stat[1].potential = p2p

        market.update(rnum + 1, p1s + p2s, p1p + p2p)

        rstats['player1pumps'].append(player1.pumps)
        rstats['player2pumps'].append(player2.pumps)
        rstats['player1sold'].append(p1s)
        rstats['player2sold'].append(p2s)
        rstats['player1potential'].append(p1p)
        rstats['player2potential'].append(p2p)
        rstats['player1revenue'].append(p1r)
        rstats['player2revenue'].append(p2r)
        rstats['player1money'].append(player1.money)
        rstats['player2money'].append(player2.money)
        rstats['oilprice'].append(market.oil_price)
        rstats['oildemand'].append(market.demand)

        stats.update({rnum: RoundStat(rnum, market.oil_price, market.demand,
                                      market.supply, p1p + p2p, stat)})
        print stats[rnum]
        print

    with open('data.txt', 'w') as f:
        for k, v in rstats.iteritems():
            print_mat(k, v, f)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

