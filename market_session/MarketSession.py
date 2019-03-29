import sys, random
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from pkg.common.Order import *
from pkg.qf_map import *


class MarketSession:

    def __init__(self, trial_id, buyers, sellers, order_schedule, market_data_receiver):
        self.orderID = 0
        self.trial_id = trial_id
        self.buyers = buyers
        self.sellers = sellers
        self.order_sched = order_schedule

        traders = {}
        traders.update(buyers)
        traders.update(sellers)
        self.traders = traders

        self.scheduler = BackgroundScheduler()
        self.market_data_receiver = market_data_receiver

    def gen_order_id(self) -> int:
        self.orderID = self.orderID + 1
        return self.orderID

    def create_limit_order(self, client_id: str = None, side=None, qty=None, price=None):
        if client_id is None:
            client_id = "HUMAN"

        if side is None:
            side = Side.BID if (random.randint(0, 1) == 0) else Side.ASK

        if qty is None:
            qty = float(random.randint(10, 50))

        if price is None:
            price = round(random.uniform(1.00, 2.00), 2)

        order = LimitOrder(self.gen_order_id(), client_id, "SMBL", side, qty, price)
        return order

    @staticmethod
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
                issuetimes[t] = min(interval * (issuetimes[t] / arrival_time), interval - 1)

        return issuetimes

    @staticmethod
    def get_sched_mode(time, schedules):
        for s in schedules:
            if (s["from"] <= time) and (time < s["to"]):
                return s['ranges'], s['stepmode']

        sys.exit('Fail: time=%s not within any timezone in os=%s' % (time, schedules))

    @staticmethod
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
            order_price = round(random.uniform(pmin, pmax), 0)
        else:
            sys.exit('FAIL: Unknown mode in schedule')

        return order_price

    def print_results(self):
        for tid in list(self.traders):
            t = self.traders[tid]
            print('%s %s N=%d B=%.2f' % (t.tid, t.t_type, t.n_trades, t.balance))

    def print_all(self):
        meta_data = {}

        # COLLATE TRADERS BY TYPE
        for t in self.traders:
            t_type = self.traders[t].t_type

            if t_type in meta_data.keys():
                balance = meta_data[t_type]['balance_sum'] + self.traders[t].balance
                n = meta_data[t_type]['count'] + 1
            else:
                balance = self.traders[t].balance
                n = 1
            meta_data[t_type] = {'count': n, 'balance_sum': balance}

        # PRINT TRADER TYPE REPORT
        for ttype in sorted(list(meta_data.keys())):
            n = meta_data[ttype]['count']
            profit = meta_data[ttype]['balance_sum']
            print('%s, TOTAL=%.2f, AVERAGE=%.2f' % (ttype, profit, profit / float(n)))

        print('\n')

    def cancel_open_orders(self):
        for t in self.traders:
            self.traders[t].cancel_all_live()

    def run(self):
        def print_time():
            time_left = (self.order_sched["end"] - datetime.now()) / (self.order_sched["end"] - self.order_sched["start"])
            print("\nTime left {:.0%}  #############################################################".format(time_left))

        def place_order():
            trader_name, trader = random.choice(list(self.traders.items()))
            tradable_order = trader.get_order(0, self.market_data_receiver.get_lob())

            if tradable_order is not None:
                trader.place_order(tradable_order)

        def distribute_new_order(t, t_id, n_traders, side, side_sched, issue_time, start_time):
            ranges, mode = self.get_sched_mode(issue_time, side_sched)

            seconds_in_experiment = issue_time - start_time
            price = self.get_order_price(t, n_traders, ranges, mode, seconds_in_experiment)

            self.traders[t_id].add_limit_order(self.create_limit_order(t_id, side, 1, price))

        def schedule_orders(side, trader_ids):
            now = datetime.now()
            side_sched = self.order_sched["dem"] if side == Side.BID else self.order_sched["sup"]

            times = self.get_issue_times(
                len(trader_ids),
                self.order_sched["timemode"],
                self.order_sched["interval"],
                True
            )
            random.shuffle(trader_ids)

            for t, t_id in enumerate(trader_ids):
                run_time = now + timedelta(seconds=times[t])

                self.scheduler.add_job(
                    distribute_new_order,
                    args=[t, t_id, len(trader_ids), side, side_sched, run_time, self.order_sched["start"]],
                    trigger='date',
                    run_date=run_time
                )

        print("Open Market: Session %d" % self.trial_id)

        self.scheduler.add_job(
            print_time,
            'interval',
            seconds=5,
            next_run_time=datetime.now()
        )

        # BUYERS
        self.scheduler.add_job(
            schedule_orders,
            args=[
                Side.BID,
                list(self.buyers.keys()),
            ],
            trigger='interval',
            seconds=self.order_sched["interval"],
            next_run_time=datetime.now()
        )

        # SELLERS
        self.scheduler.add_job(
            schedule_orders,
            args=[
                Side.ASK,
                list(self.sellers.keys())
            ],
            trigger='interval',
            seconds=self.order_sched["interval"],
            next_run_time=datetime.now()
        )

        # SEND TO EXCHANGE
        self.scheduler.add_job(
            place_order,
            trigger='interval',
            seconds=0.05,
        )

        self.scheduler.start()

        while datetime.now() < self.order_sched["end"]:
            time.sleep(1)

        self.scheduler.shutdown()
        print("\nEND OF MARKET SESSION")

        print("\nCANCELLING LIVE ORDERS")
        self.cancel_open_orders()

        print("\nREPORT")
        self.print_results()
        self.print_all()
