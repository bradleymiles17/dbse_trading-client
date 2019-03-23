import sys, random, argparse, math, schedule
from fix_application.FixClient import FixClient
from pkg.common.Order import *
from pkg.qf_map import *
from traders.TraderGiveaway import TraderGiveaway
from traders.TraderZIC import TraderZIC


orderID = 0


def gen_order_id() -> int:
    global orderID
    orderID = orderID + 1
    return orderID


def create_limit_order(client_id: str=None, side=None, qty=None, price=None):
    if client_id is None:
        client_id = "HUMAN"

    if side is None:
        side = Side.BID if (random.randint(0, 1) == 0) else Side.ASK

    if qty is None:
        qty = float(random.randint(10, 50))

    if price is None:
        price = round(random.uniform(1.00, 2.00), 2)

    order = LimitOrder(gen_order_id(), client_id, "SMBL", side, qty, price)
    return order


# create a bunch of traders from traders_spec
# returns tuple (n_buyers, n_sellers)
# optionally shuffles the pack of buyers and the pack of sellers
def populate_market(traders_spec, pre_name, fix_client: FixClient):

    def trader_type(robot_type, name):
        if robot_type == 'GVWY':
            return TraderGiveaway('GVWY', name, 0.00, fix_client)
        # elif robot_type == 'ZIC':
        #     return TraderZIC('ZIC', name, 0.00, fix_client)
        # elif robot_type == 'SHVR':
        #     return TraderShaver('SHVR', name, 0.00, fix_client)
        # elif robot_type == 'SNPR':
        #     return TraderSniper('SNPR', name, 0.00, fix_client)
        # elif robot_type == 'ZIP':
        #     return TraderZIP('ZIP', name, 0.00, fix_client)
        else:
            sys.exit('FATAL: don\'t know robot type %s\n' % robot_type)

    traders = {}

    for bs in traders_spec:
        for count in range(bs[1]):
            name = pre_name + '%02d' % len(traders)
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
        print("\nTime left {:.0%}".format(time_left))

    def distribute_new_order(buyers, sellers):
        print("\n")
        buyer_id, _ = random.choice(list(buyers.items()))
        seller_id, _ = random.choice(list(sellers.items()))

        traders[buyer_id].add_limit_order(create_limit_order(buyer_id, Side.BID))
        traders[seller_id].add_limit_order(create_limit_order(seller_id, Side.ASK))

    def place_order(traders):
        print("\n")
        trader_name, trader = random.choice(list(traders.items()))
        tradable_order = trader.get_order(0, {})

        if tradable_order is not None:
            trader.place_order(tradable_order)

    schedule.every(5).seconds.do(print_time)
    schedule.every(1).seconds.do(distribute_new_order, buyers, sellers)
    schedule.every(1).seconds.do(place_order, traders)

    while time.time() < end_time:
        schedule.run_pending()

    schedule.clear()
    print("End of market session\n")
    return 1


def build_traders():
    # buyers_spec = [('GVWY', 10), ('SHVR', 10), ('ZIC', 10), ('ZIP', 10)]
    buyers_spec = [('GVWY', 10)]
    sellers_spec = buyers_spec
    traders_spec = {'sellers': sellers_spec, 'buyers': buyers_spec}

    buyers = populate_market(traders_spec['buyers'], 'B', fix_client)
    sellers = populate_market(traders_spec['sellers'], 'S', fix_client)

    return buyers, sellers


def build_order_schedule(start_time, end_time):

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

    return order_sched


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

        buyers, sellers = build_traders()

        traders = {}
        traders.update(buyers)
        traders.update(sellers)
        fix_client.traders = traders

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
                start_time = time.time()
                end_time = start_time + 60

                order_sched = build_order_schedule(start_time, end_time)

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
