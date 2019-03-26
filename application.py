import sys, random, argparse, math
from datetime import datetime, timedelta

from fix.FixClient import FixClient
from pkg.common.Order import *
from pkg.qf_map import *
from traders.TraderGiveaway import TraderGiveaway
from apscheduler.schedulers.background import BackgroundScheduler
from traders.TraderZIC import TraderZIC

orderID = 0


def gen_order_id() -> int:
    global orderID
    orderID = orderID + 1
    return orderID


def create_limit_order(client_id: str = None, side=None, qty=None, price=None):
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


def get_issue_times(n_traders, mode, interval, fit_to_interval):
    interval = float(interval)

    if n_traders < 1:
        sys.exit('FAIL: n_traders < 1 in getissuetime()')
    elif n_traders == 1:
        t_step = interval
    else:
        t_step = interval / (n_traders - 1)

    arrival_time = 0
    issuetimes = []

    for t in range(n_traders):
        if mode == 'periodic':
            arrival_time = interval
        elif mode == 'drip-fixed':
            arrival_time = t * t_step
        elif mode == 'drip-jitter':
            arrival_time = t * t_step + t_step * random.random()
        elif mode == 'drip-poisson':
            # poisson requires a bit of extra work
            interarrivaltime = random.expovariate(n_traders / interval)
            arrival_time += interarrivaltime
        else:
            sys.exit('FAIL: unknown time-mode in getissuetimes()')
        issuetimes.append(arrival_time)

    # at this point, arrtime is the last arrival time
    if fit_to_interval and ((arrival_time > interval) or (arrival_time < interval)):
        # generated sum of interarrival times longer than the interval
        # squish them back so that last arrival falls at t=interval
        for t in range(n_traders):
            issuetimes[t] = min(interval * (issuetimes[t] / arrival_time), interval-1)

    return issuetimes


def get_sched_mode(time, schedules):
    for s in schedules:
        if (s["from"] <= time) and (time < s["to"]):
            return s['ranges'], s['stepmode']

    sys.exit('Fail: time=%s not within any timezone in os=%s' % (time, schedules))


def get_order_price(i, n_traders, ranges, mode, seconds_in_experiment):
    # does the first schedule range include optional dynamic offset function(s)?
    if len(ranges[0]) > 2:
        offsetfn = ranges[0][2]
        if callable(offsetfn):
            # same offset for min and max
            offset_min = offsetfn(seconds_in_experiment.total_seconds())
            offset_max = offset_min
        else:
            sys.exit('FAIL: 3rd argument of sched in getorderprice() not callable')

        if len(ranges[0]) > 3:
            # if second offset function is specfied, that applies only to the max value
            offsetfn = ranges[0][3]
            if callable(offsetfn):
                # this function applies to max
                offset_max = offsetfn(seconds_in_experiment.total_seconds())
            else:
                sys.exit('FAIL: 4th argument of sched in getorderprice() not callable')
    else:
        offset_min = 0.0
        offset_max = 0.0

    pmin = offset_min + min(ranges[0][0], ranges[0][1])
    pmax = offset_max + max(ranges[0][0], ranges[0][1])
    prange = pmax - pmin
    stepsize = prange / (n_traders - 1)
    halfstep = round(stepsize / 2.0)

    if mode == 'fixed':
        order_price = pmin + int(i * stepsize)
    elif mode == 'jittered':
        order_price = pmin + int(i * stepsize) + random.randint(-halfstep, halfstep)
    elif mode == 'random':
        if len(ranges) > 1:
            # more than one schedule: choose one equiprobably
            s = random.randint(0, len(ranges) - 1)
            pmin = min(ranges[s][0], ranges[s][1])
            pmax = max(ranges[s][0], ranges[s][1])
        order_price = round(random.uniform(pmin, pmax), 2)
    else:
        sys.exit('FAIL: Unknown mode in schedule')

    return order_price


def market_session(trial_id, buyers, sellers, order_sched):

    def print_time():
        time_left = (order_sched["end"] - datetime.now()) / (order_sched["end"] - order_sched["start"])
        print("\nTime left {:.0%}".format(time_left))

    def place_order(traders):
        trader_name, trader = random.choice(list(traders.items()))
        tradable_order = trader.get_order(0, {})

        if tradable_order is not None:
            trader.place_order(tradable_order)

    def distribute_new_order(t, t_id, n_traders, side, side_sched, issue_time, start_time):
        ranges, mode = get_sched_mode(issue_time, side_sched)

        seconds_in_experiment = issue_time - start_time
        price = get_order_price(t, n_traders, ranges, mode, seconds_in_experiment)

        traders[t_id].add_limit_order(create_limit_order(t_id, side, 1, price))

    def schedule_orders(order_sched, side, trader_ids):
        now = datetime.now()
        side_sched = order_sched["dem"] if side == Side.BID else order_sched["sup"]

        times = get_issue_times(
            len(trader_ids),
            order_sched["timemode"],
            order_sched["interval"],
            True
        )
        random.shuffle(trader_ids)

        for t, t_id in enumerate(trader_ids):
            run_time = now + timedelta(seconds=times[t])

            scheduler.add_job(
                distribute_new_order,
                args=[t, t_id, len(trader_ids), side, side_sched, run_time, order_sched["start"]],
                trigger='date',
                run_date=run_time
            )

    print("Open Market: Session %d" % trial_id)

    traders = {}
    traders.update(buyers)
    traders.update(sellers)

    scheduler = BackgroundScheduler()

    scheduler.add_job(
        print_time,
        'interval',
        seconds=5,
        next_run_time=datetime.now()
    )

    # BUYERS
    scheduler.add_job(
        schedule_orders,
        args=[
            order_sched,
            Side.BID,
            list(buyers.keys()),
        ],
        trigger='interval',
        seconds=order_sched["interval"],
        next_run_time=datetime.now()
    )

    # SELLERS
    scheduler.add_job(
        schedule_orders,
        args=[
            order_sched,
            Side.ASK,
            list(sellers.keys())
        ],
        trigger='interval',
        seconds=order_sched["interval"],
        next_run_time=datetime.now()
    )

    scheduler.add_job(
        place_order,
        args=[traders],
        trigger='interval',
        seconds=1,
    )

    scheduler.start()

    while datetime.now() < end_time:
        time.sleep(1)

    scheduler.shutdown()
    print("End of market session\n")

    print_results(traders)
    return 1


def print_results(traders):
    print("REPORT")
    profit = 0.0
    for tid in list(traders):
        t = traders[tid]
        profit += t.balance
        print('%s %s N=%d B=%.2f' % (t.tid, t.t_type, t.n_trades, t.balance))

    print("TOTAL PROFIT = %.2f" % profit)
    print("AVERAGE PROFIT = %.2f" % (profit/len(traders)))


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

    range1 = (110.0, 120.0)
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
        end_time_seconds = 60.0

        # buyers_spec = [('GVWY', 10), ('SHVR', 10), ('ZIC', 10), ('ZIP', 10)]
        buyers_spec = [('GVWY', 10)]
        sellers_spec = buyers_spec
        traders_spec = {'sellers': sellers_spec, 'buyers': buyers_spec}

        buyers = populate_market(traders_spec['buyers'], 'B', fix_client)
        sellers = populate_market(traders_spec['sellers'], 'S', fix_client)

        traders = {}
        traders.update(buyers)
        traders.update(sellers)
        fix_client.traders = traders

        while 1:
            input_str = input()
            if input_str == "market":
                start_time = datetime.now() + timedelta(seconds=start_time_seconds)
                end_time = start_time + timedelta(seconds=end_time_seconds)

                order_sched = build_order_schedule(start_time, end_time)
                market_session(trial_id, buyers, sellers, order_sched)
            if input_str == '4':
                sys.exit(0)
            if input_str == 'd':
                import pdb

                pdb.set_trace()
            else:
                continue
    except (fix.ConfigError, fix.RuntimeError) as e:
        print(e)
