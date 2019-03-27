import math, sys, argparse
import quickfix as fix

from datetime import datetime, timedelta
from fix.FixClient import FixClient
from market_data.MarketDataReceiver import MarketDataReceiver
from market_session.MarketSession import MarketSession

from traders.TraderGiveaway import TraderGiveaway
from traders.TraderShaver import TraderShaver
from traders.TraderZIC import TraderZIC


# create a bunch of traders from traders_spec
# returns tuple (n_buyers, n_sellers)
# optionally shuffles the pack of buyers and the pack of sellers
def populate_market(traders_spec, pre_name, fix_client: FixClient):
    def trader_type(robot_type, name):
        if robot_type == 'GVWY':
            return TraderGiveaway('GVWY', name, 0.00, fix_client)
        elif robot_type == 'ZIC':
            return TraderZIC('ZIC', name, 0.00, fix_client)
        elif robot_type == 'SHVR':
            return TraderShaver('SHVR', name, 0.00, fix_client)
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


def build_order_schedule(start_time, end_time):

    # schedule_offsetfn returns time-dependent offset on schedule prices
    def schedule_offsetfn(t):
        pi2 = math.pi * 2
        c = math.pi * 3000
        wavelength = t / c
        gradient = 100 * t / (c / pi2)
        amplitude = 100 * t / (c / pi2)
        offset = gradient + amplitude * math.sin(wavelength * t)
        return int(round(offset, 0))

    range1 = (90.0, 120.0)
    demand_schedule = [
        {
            'from': start_time,
            'to': end_time,
            'ranges': [range1],
            'stepmode': 'fixed'
        }
    ]

    range1 = (105.0, 140.0)
    supply_schedule = [
        {
            'from': start_time,
            'to': end_time,
            'ranges': [range1],
            'stepmode': 'fixed'
        }
    ]

    order_sched = {
        'dem': demand_schedule,
        'sup': supply_schedule,
        'start': start_time,
        'end': end_time,
        'interval': 30,
        'timemode': 'drip-poisson'
    }

    return order_sched


if __name__ == '__main__':

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
        trial_id = 0
        start_time_seconds = 0.0
        end_time_seconds = 300.0

        # buyers_spec = [('GVWY', 10), ('SHVR', 10), ('ZIC', 10), ('ZIP', 10)]
        buyers_spec = [('GVWY', 5), ('SHVR', 5), ('ZIC', 5)]
        sellers_spec = buyers_spec
        traders_spec = {'sellers': sellers_spec, 'buyers': buyers_spec}

        buyers = populate_market(traders_spec['buyers'], 'B', fix_client)
        sellers = populate_market(traders_spec['sellers'], 'S', fix_client)

        traders = {}
        traders.update(buyers)
        traders.update(sellers)
        fix_client.traders = traders

        # Launch market data receiver
        market_data_receiver = MarketDataReceiver()

        while 1:
            print("\nENTER COMMAND")
            input_str = input()
            if input_str == "market":
                start_time = datetime.now() + timedelta(seconds=start_time_seconds)
                end_time = start_time + timedelta(seconds=end_time_seconds)

                order_schedule = build_order_schedule(start_time, end_time)
                session = MarketSession(trial_id, buyers, sellers, order_schedule, market_data_receiver)
                session.run()
            if input_str == '4':
                sys.exit(0)
            if input_str == 'd':
                import pdb

                pdb.set_trace()
            else:
                continue
    except (fix.ConfigError, fix.RuntimeError) as e:
        print(e)
