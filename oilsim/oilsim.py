#!/usr/bin/env python

from __future__ import division, with_statement

from collections import defaultdict
from math import cos, sin, pi, log, ceil

import random
import os
import os.path
import sys

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
        p1r, p1s, p1p, p2r, p2s, p2p, p1st, p2st = market.revenue(player1, player2)
        self.pm['00'] = (p1r, p2r)
        p1r = 0
        p2r = 0
        
        p1rt, p1s, p1p, p2rt, ps2, p2p, p1st, p2st = market.revenue(player1, player2, -1, -1)
        self.pm['SS'] = (p1rt - p1r + market.pump_sell_price, p2rt - p2r + market.pump_sell_price)

        p1rt, p1s, p1p, p2rt, ps2, p2p, p1st, p2st = market.revenue(player1, player2, -1, 0)
        self.pm['S0'] = (p1rt - p1r + market.pump_sell_price, p2rt - p2r)
        
        p1rt, p1s, p1p, p2rt, ps2, p2p, p1st, p2st = market.revenue(player1, player2, -1, 1)
        self.pm['SB'] = (p1rt - p1r + market.pump_sell_price, p2rt - p2r - market.pump_buy_price)

        p1rt, p1s, p1p, p2rt, ps2, p2p, p1st, p2st = market.revenue(player1, player2, 0, -1)
        self.pm['0S'] = (p1rt - p1r, p2rt - p2r + market.pump_sell_price)

        p1rt, p1s, p1p, p2rt, ps2, p2p, p1st, p2st = market.revenue(player1, player2, 0, 1)
        self.pm['0B'] = (p1rt - p1r, p2rt - p2r - market.pump_buy_price)

        p1rt, p1s, p1p, p2rt, ps2, p2p, p1st, p2st = market.revenue(player1, player2, 1, -1)
        self.pm['BS'] = (p1rt - p1r - market.pump_buy_price , p2rt - p2r + market.pump_sell_price)

        p1rt, p1s, p1p, p2rt, ps2, p2p, p1st, p2st = market.revenue(player1, player2, 1, 0)
        self.pm['B0'] = (p1rt - p1r - market.pump_buy_price, p2rt - p2r)
        
        p1rt, p1s, p1p, p2rt, ps2, p2p, p1st, p2st = market.revenue(player1, player2, 1, 1)
        self.pm['BB'] = (p1rt - p1r - market.pump_buy_price, p2rt - p2r - market.pump_buy_price)

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
        self.stash = 0
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
            print '... but cannot afford it'
            return False

    def sell_pump(self, market):
        print '%s sells a pump.' % self.name
        if self.pumps > 0:
            self.dpumps -= 1
            self.money += market.pump_sell_price
            return True
        else:
            print "... but doesn't own any pumps."
            return False

    def begin_round(self):
        self.pumps += self.dpumps
        self.dpumps = 0
        self.oldmoney = self.money

    def end_round(self, revenue, stash=0):
        self.money += revenue
        self.dmoney = self.money - self.oldmoney
        self.stash = stash

    def __str__(self):
        return self.name

class Strategy(object):
    def __init__(self, producer):
        self.producer = producer

    def begin_round(self):
        self.producer.begin_round()

    def end_round(self, revenue, output, stash=0):
        self.producer.end_round(revenue, stash)
        return PlayerStat(self.producer.name, self.producer.money,
                          self.producer.dmoney, self.producer.pumps,
                          output)

    def perform(self, d, market):
        if d == 'S':
            return self.producer.sell_pump(market)
        elif d == 'B':
            return self.producer.buy_pump(market)
        return True

    name = property(lambda self: self.producer.name)
    pumps = property(lambda self: self.producer.pumps)
    money = property(lambda self: self.producer.money)
    stash = property(lambda self: self.producer.stash)

class RandomStrategy(Strategy):
    def __init__(self, producer):
        Strategy.__init__(self, producer)

    def decide(self, pm, market):
        d = ['S', 'B', '0']
        random.shuffle(d)
        return d

def maxl(l):
    return max(x[0] for x in l)

def minl(l):
    return min(x[0] for x in l)

class TakeBestStrategy(Strategy):
    def __init__(self, producer):
        Strategy.__init__(self, producer)

    def decide(self, pm, market):
        b = maxl(pm.getdata(self, 'B'))
        z = maxl(pm.getdata(self, '0'))
        s = maxl(pm.getdata(self, 'S'))
        m = max(b, z, s)
        if m == b:
            m = max(z, s)
            if m == z:
                return ('B', '0', 'S')
            else:
                return ('B', 'S', '0')
        elif m == s:
            m = max(b, z)
            if m == b:
                return ('S', 'B', '0')
            else:
                return ('S', '0', 'B')
        else:
            return ('0', 'B', 'S')

class MinmaxStrategy(Strategy):
    def __init__(self, producer):
        Strategy.__init__(self, producer)

    def decide(self, pm, market):
        b = minl(pm.getdata(self, 'B'))
        bm = maxl(pm.getdata(self, 'B'))
        z = minl(pm.getdata(self, '0'))
        zm = maxl(pm.getdata(self, '0'))
        s = minl(pm.getdata(self, 'S'))
        sm = maxl(pm.getdata(self, 'S'))

        m = max(b, z, s)
        if b == z and z == s:
            if bm == zm and zm == sm:
                return ('B', '0', 'S')
            m = max(bm, zm, sm)
            if m == bm:
                if max(zm, sm) == zm:
                    return ('B', '0', 'S')
                else:
                    return ('B', 'S', '0')
            elif m == zm:
                return ('0', 'B', 'S')
            else:
                if max(zm, bm) == zm:
                    return ('S', '0', 'B')
                else:
                    return ('S', 'B', '0')
        elif m == z and m == s:
            if max(zm, sm) == zm:
                return ('0', 'S', 'B')
            else:
                return ('S', '0', 'B')
        elif m == b and m == s:
            if max(bm, sm) == bm:
                return ('B', 'S', '0')
            else:
                return ('S', 'B', '0')
        elif m == b and m == z:
            if max(bm, zm) == bm:
                return ('B', '0', 'S')
            else:
                return ('0', 'B', 'S')
        elif m == b:
            if max(s, z) == z:
                return 'B0S'
            else:
                return 'BS0'
        elif m == s:
            if max(b, z) == z:
                return 'S0B'
            else:
                return 'SB0'
        else:
            return '0BS'

class DoNothingStrategy(Strategy):
    def __init__(self, producer):
        Strategy.__init__(self, producer)

    def decide(self, *args):
        return '0BS'

class SimpleOilPriceModel(object):
    def __init__(self, factor):
        self.factor = factor

    def update(self, round, demand, act_supply, supply):
        try:
            self.price = min(self.factor * demand / supply, self.factor / 0.05)
        except ZeroDivisionError:
            self.price = self.factor / 0.05

class ConstantDemandModel(object):
    def __init__(self, demand=200):
        self.demand = demand

    def update(self, *args):
        pass

class LinearDemandModel(object):
    def __init__(self, d=200, k=1/10):
        self.d = d
        self.k = k

    def update(self, round, *args):
        self.demand = self.k * round + self.d

class LinearCosDemandModel(object):
    def __init__(self, d=200, k=1/10, alpha=1/12):
        self.d = d
        self.k = k
        self.alpha = alpha

    def update(self, round, *args):
        self.demand = self.k * cos(self.alpha * pi * round) + self.d

class ConstantPumpModel(object):
    def __init__(self, buy_price, sell_price, maintenance_cost, output):
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.maintenance_cost = maintenance_cost
        self.output = output

    def update(self, *args):
        pass

class LogPumpModel(object):
    def __init__(self, buy_price, sell_price, start_maintenance_cost, total_oil, output):
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.smc = start_maintenance_cost
        self.sto = 1000*log(total_oil)
        self.output = output

    def update(self, round, demand, supply, potential, total_oil):
        self.maintenance_cost = -1000*log(total_oil) + self.smc + self.sto

class ConstantStashModel(object):
    def __init__(self, tank_price, tank_size):
        self.size = tank_size
        self.tank_price = tank_price

    def price(self, stash):
        return ceil(stash / self.size) * self.tank_price

class Market(object):
    def __init__(self, total_oil, oil_model, pump_model, demand_model, stash_model):
        self.total_oil = total_oil
        self.oil_model = oil_model
        self.pump_model = pump_model
        self.demand_model = demand_model
        self.stash_model = stash_model
    
    def update(self, round, act_supply, supply):
        self.round = round
        self.supply = supply
        self.act_supply = act_supply
        self.total_oil -= act_supply
        if self.total_oil <= 0:
            return False

        self.demand_model.update(round, act_supply, supply)
        self.oil_model.update(round, self.demand, act_supply, supply)
        self.pump_model.update(round, self.demand, act_supply, supply, self.total_oil)
        return True
       
    demand = property(lambda self: self.demand_model.demand)
    oil_price = property(lambda self: self.oil_model.price)
    pump_buy_price = property(lambda self: self.pump_model.buy_price)
    pump_sell_price = property(lambda self: self.pump_model.sell_price)
    pump_output = property(lambda self: self.pump_model.output)
    pump_maintenance_cost = property(lambda self: self.pump_model.maintenance_cost)

    def revenue(self, player1, player2, pd1=0, pd2=0):
        """ Calculate revenues of player 1 and 2 based on their pumps. """
        pumpsp1 = player1.pumps + pd1
        pumpsp2 = player2.pumps + pd2
        stash1 = player1.stash
        stash2 = player2.stash

        if pumpsp1 + pumpsp2 == 0:
            return (0, 0, 0, 0, 0, 0, 0, 0)

        # calculate the relative sizes
        p1s = pumpsp1 / (pumpsp1 + pumpsp2)
        p2s = 1 - p1s
        
        # oil produced per player
        p1o = pumpsp1 * self.pump_output
        p2o = pumpsp2 * self.pump_output

        # amount of sold oil (total and per player)
        oilsold = min(p1o + p2o + stash1 + stash2, self.demand)
        p1s = p1s * oilsold
        p2s = p2s * oilsold

        if p1s > p1o + stash1:
            d = p1o + stash1 - p1s
            p1s = p1o + stash1
            p2s += d
            assert p2s <= p2o + stash2
        elif p2s > p2o + stash2:
            d = p2o +stash2 - p2s
            p2s = p2o + stash2
            p1s += d
            assert p1s <= p1o + stash1

        stash1 = max(0, stash1 + p1o - p1s)
        stash2 = max(0, stash2 + p2o - p2s)

        # revene of both players
        if pd1 != 0 or pd2 != 0:
            self.oil_model.update(self.round + 1, self.demand, p1s + p2s, p1o + p2o + stash1 + stash2)

        p1r = self.oil_price * p1s - self.pump_maintenance_cost * pumpsp1 - self.stash_model.price(stash1)
        p2r = self.oil_price * p2s - self.pump_maintenance_cost * pumpsp2 - self.stash_model.price(stash2)

        self.oil_model.update(self.round, self.demand, self.act_supply, self.supply)
        return (p1r, p1s, p1o, p2r, p2s, p2o, stash1, stash2)

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

""" price of a new pump """
PUMP_BUY_PRICE = 1000
""" value of an pump """
PUMP_SELL_PRICE = PUMP_BUY_PRICE/2
""" liters of oil produced by one pump / per month """
PUMP_OUTPUT = 100
""" total amount of rounds to play (note: 1 round = 1 month) """
ROUNDS = 5000*12 # 1000*12
""" the cost of operationg a pump per month """
PUMP_MAINTENANCE_COST = 100
OIL_SOURCE_SIZE = 20000*1000

def main():
    opm = SimpleOilPriceModel(10)
    # pm = ConstantPumpModel(PUMP_BUY_PRICE, PUMP_SELL_PRICE, PUMP_MAINTENANCE_COST, PUMP_OUTPUT)
    pm = LogPumpModel(PUMP_BUY_PRICE, PUMP_SELL_PRICE, PUMP_MAINTENANCE_COST, OIL_SOURCE_SIZE, PUMP_OUTPUT)
    market = Market(OIL_SOURCE_SIZE, opm, pm, LinearDemandModel(2000,0), ConstantStashModel(PUMP_BUY_PRICE/10, 10*PUMP_BUY_PRICE))
    producer1 = OilProducer(0, 10000, 'Player 1')
    producer2 = OilProducer(1, 10000, 'Player 2')
    player1 = MinmaxStrategy(producer1) # RandomStrategy(producer1)
    player2 = MinmaxStrategy(producer2) # RandomStrategy(producer2)
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

        for d in p1d:
            if player1.perform(d, market):
                break
        for d in p2d:
            if player2.perform(d, market):
                break

        # revenue, oil sold, potential
        p1r, p1s, p1p, p2r, p2s, p2p, p1st, p2st = market.revenue(player1, player2)
        stat = [player1.end_round(p1r, p1s, p1st), player2.end_round(p2r, p2s, p2st)]
        stat[0].potential = p1p
        stat[1].potential = p2p

        if not market.update(rnum + 1, p1s + p2s, p1p + p2p + player1.stash + player2.stash):
            print "oil source is empty"
            break

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
        rstats['player1stash'].append(player1.stash)
        rstats['player2stash'].append(player2.stash)
        rstats['oilsource'].append(market.total_oil)
        rstats['pumpmaintcost'].append(market.pump_maintenance_cost)

        stats.update({rnum: RoundStat(rnum, market.oil_price, market.demand,
                                      market.supply, p1p + p2p, stat)})
        print stats[rnum]
        print

    if os.path.exists('data.txt'):
        s = os.stat('data.txt')
        os.rename('data.txt', 'data.%d.txt' % s.st_mtime)
    with open('data.txt', 'w') as f:
        for k, v in rstats.iteritems():
            print_mat(k, v, f)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

