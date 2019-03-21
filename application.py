import sys, random, argparse, math, schedule

from traders.Trader_Giveaway import Trader_Giveaway
from fix_application.FixClient import FixClient
from pkg.common.Order import *
from pkg.qf_map import *


def create_limit_order(side=None, qty=None, price=None):
    if side is None:
        side = Side.BID if (random.randint(0, 1) == 0) else Side.ASK

    if qty is None:
        qty = float(random.randint(10, 50))

    if price is None:
        price = round(random.uniform(1.00, 2.00), 2)

    return LimitOrder("SMBL", side, qty, price)


# create a bunch of traders from traders_spec
# returns tuple (n_buyers, n_sellers)
# optionally shuffles the pack of buyers and the pack of sellers
def populate_market(traders_spec, pre_name, fix_client: FixClient):

    def trader_type(robot_type, name):
        if robot_type == 'GVWY':
            return Trader_Giveaway('GVWY', name, 0.00, fix_client)
        # elif robot_type == 'ZIC':
        #     return Trader_ZIC('ZIC', name, 0.00, 0)
        # elif robot_type == 'SHVR':
        #     return Trader_Shaver('SHVR', name, 0.00, 0)
        # elif robot_type == 'SNPR':
        #     return Trader_Sniper('SNPR', name, 0.00, 0)
        # elif robot_type == 'ZIP':
        #     return Trader_ZIP('ZIP', name, 0.00, 0)
        else:
            sys.exit('FATAL: don\'t know robot type %s\n' % robot_type)

    traders = {}

    for bs in traders_spec:
        for count in range(bs[1]):
            name = pre_name + '%02d' % count
            traders[name] = trader_type(bs[0], name)

    if len(traders) < 1:
        sys.exit('FATAL: no buyers specified\n')

    return traders


def market_session(trial_id, start_time, end_time, buyers, sellers, order_sched):
    traders = {}
    traders.update(buyers)
    traders.update(sellers)

    def print_time():
        time_left = (end_time - time.time()) / (end_time - start_time)
        print("Time left {:.0%}".format(time_left))

    def distribute_new_order(traders):
        trader_name, _ = random.choice(list(traders.items()))

        order = create_limit_order()
        traders[trader_name].add_order(order)

    def place_order(traders):
        trader_name, trader = random.choice(list(traders.items()))
        tradable_order = trader.get_order(0, {})
        if tradable_order is not None:
            fix_client.place_order(tradable_order)

    schedule.every(5).seconds.do(print_time)
    schedule.every(1).seconds.do(distribute_new_order, traders)
    schedule.every(1).seconds.do(place_order, traders)

    while time.time() < end_time:
        schedule.run_pending()

    return 1


if __name__ == '__main__':

    # schedule_offsetfn returns time-dependent offset on schedule prices
    def schedule_offsetfn(t):
        pi2 = math.pi * 2
        c = math.pi * 3000
        wavelength = t / c
        gradient = 100 * t / (c / pi2)
        amplitude = 100 * t / (c / pi2)
        offset = gradient + amplitude * math.sin(wavelength * t)
        return int(round(offset, 0))


    parser = argparse.ArgumentParser(description='FIX Server')
    parser.add_argument('file_name', type=str, help='Name of configuration file')
    args = parser.parse_args()

    try:
        settings = fix.SessionSettings(args.file_name)
        fix_client = FixClient()
        storeFactory = fix.FileStoreFactory(settings)
        logFactory = fix.FileLogFactory(settings)
        initiator = fix.SocketInitiator(fix_client, storeFactory, settings, logFactory)
        initiator.start()

        # CONFIGURATION

        start_time = time.time()
        end_time = start_time + 60

        range1 = (95, 95, schedule_offsetfn)
        supply_schedule = [
            {
                'from': start_time,
                'to': end_time,
                'ranges': [range1],
                'stepmode': 'fixed'
            }
        ]

        range1 = (105, 105, schedule_offsetfn)
        demand_schedule = [
            {
                'from': start_time,
                'to': end_time,
                'ranges': [range1],
                'stepmode': 'fixed'
            }
        ]

        order_sched = {
            'sup': supply_schedule,
            'dem': demand_schedule,
            'interval': 30,
            'timemode': 'drip-poisson'
        }

        # buyers_spec = [('GVWY', 10), ('SHVR', 10), ('ZIC', 10), ('ZIP', 10)]
        buyers_spec = [('GVWY', 10)]
        sellers_spec = buyers_spec
        traders_spec = {'sellers': sellers_spec, 'buyers': buyers_spec}

        while 1:
            input_str = input()
            if input_str == 'b':
                fix_client.place_order(create_limit_order(Side.BID, 10, 1.20))
                fix_client.place_order(create_limit_order(Side.BID, 10, 1.10))
                fix_client.place_order(create_limit_order(Side.BID, 10, 1.50))
            if input_str == 'b_all':
                fix_client.place_order(create_limit_order(Side.BID, 2000, 2.00))
            if input_str == 'a':
                fix_client.place_order(create_limit_order(Side.ASK, 10, 1.50))
                fix_client.place_order(create_limit_order(Side.ASK, 10, 1.70))
                fix_client.place_order(create_limit_order(Side.ASK, 10, 1.20))
                fix_client.place_order(create_limit_order(Side.ASK, 10, 1.70))
            if input_str == 'r':
                # time + seconds
                t_end = time.time() + 30
                while time.time() < t_end:
                    fix_client.place_order(create_limit_order())
                    time.sleep(0.01)
            if input_str == "market":
                buyers = populate_market(traders_spec['buyers'], 'B', fix_client)
                sellers = populate_market(traders_spec['sellers'], 'S', fix_client)
                market_session(1, start_time, end_time, buyers, sellers, order_sched)
            if input_str == '4':
                sys.exit(0)
            if input_str == 'd':
                import pdb

                pdb.set_trace()
            else:
                continue
    except (fix.ConfigError, fix.RuntimeError) as e:
        print(e)
