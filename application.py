import argparse
import json

import quickfix as fix

from fix_engine.FixClient import FixClient
from market_data.MarketDataReceiverUDP_Unicast import MarketDataReceiver
from market_simulation.MarketSession import MarketSession
from traders.TraderGiveaway import TraderGiveaway
from traders.TraderShaver import TraderShaver
from traders.TraderSniper import TraderSniper
from traders.TraderZIC import TraderZIC


# create a bunch of traders from traders_spec
# returns tuple (n_buyers, n_sellers)
# optionally shuffles the pack of buyers and the pack of sellers
def populate_market(traders_spec, pre_name, verbose, fix_client: FixClient):
    def trader_type(robot_type, name):
        if robot_type == 'GVWY':
            return TraderGiveaway('GVWY', name, 0.00, verbose, fix_client)
        elif robot_type == 'ZIC':
            return TraderZIC('ZIC', name, 0.00, verbose, fix_client)
        elif robot_type == 'SHVR':
            return TraderShaver('SHVR', name, 0.00, verbose, fix_client)
        elif robot_type == 'SNPR':
            return TraderSniper('SNPR', name, 0.00, verbose, fix_client)
        # elif robot_type == 'ZIP':
        #     return TraderZIP('ZIP', name, 0.00, fix_client)
        else:
            sys.exit('FATAL: don\'t know robot type %s\n' % robot_type)

    traders = {}

    for robot_type in traders_spec:
        for count in range(traders_spec[robot_type]):
            name = "%s%02d_%s" % (pre_name, len(traders), robot_type)
            traders[name] = trader_type(robot_type, name)

    if len(traders) < 1:
        sys.exit('FATAL: no buyers specified\n')

    return traders

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Bristol Stock Exchange')
    parser.add_argument('fix_config', type=str, help='FIX configuration file')
    parser.add_argument('market_config', type=str, help='Market Session configuration file')
    parser.add_argument("-d", "--duration", type=float, default=300, help="duration of market session in seconds")
    parser.add_argument("-s", "--sync", default=False, help="synchronize traders to next minute", action="store_true")
    parser.add_argument("-t", "--trader", default=False, help="increase trader output verbosity", action="store_true")
    parser.add_argument("-m", "--market", default=False, help="increase market output verbosity", action="store_true")
    parser.add_argument("-f", "--fix", default=False, help="increase fix output verbosity", action="store_true")
    args = parser.parse_args()

    with open(args.market_config, 'r') as f:
        config = json.load(f)

    try:
        settings = fix.SessionSettings(args.fix_config)
        fix_client = FixClient(args.fix)
        storeFactory = fix.FileStoreFactory(settings)
        logFactory = fix.FileLogFactory(settings)
        initiator = fix.SocketInitiator(fix_client, storeFactory, settings, logFactory)
        initiator.start()

        buyers = populate_market(config["traders"]['buyers'], 'B', args.trader, fix_client)
        sellers = populate_market(config["traders"]['sellers'], 'S', args.trader, fix_client)

        traders = {}
        traders.update(buyers)
        traders.update(sellers)
        fix_client.traders = traders

        market_session = MarketSession(
            0,
            args.sync,
            args.duration,
            buyers,
            sellers,
            config["order_schedule"],
        )

        market_data_receiver = MarketDataReceiver(args.market, market_session.place_order)
        market_data_receiver.run()
        market_session.run()

    except (fix.ConfigError, fix.RuntimeError) as e:
        print(e)
