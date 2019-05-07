import random
import sys
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from pkg.common.Order import *
from pkg.qf_map import *


class MarketSession:

    def __init__(self, trial_id, start_time_delay, duration, buyers, sellers, order_schedule):
        self.start_time = datetime.now().replace(microsecond=0) + timedelta(seconds=start_time_delay)
        self.end_time = self.start_time + timedelta(seconds=duration)
        self.orderID = 0
        self.trial_id = trial_id
        self.buyers = buyers
        self.sellers = sellers
        self.order_sched = order_schedule

        traders = {}
        traders.update(buyers)
        traders.update(sellers)
        self.traders = traders
        self.traders_keys = list(self.traders.keys())

        self.scheduler = BackgroundScheduler()

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
                issuetimes[t] = min(interval * (issuetimes[t] / arrival_time), interval)

        return issuetimes

    @staticmethod
    def get_sched_mode(session_time, schedules):
        for s in schedules:
            if (s["from"] < session_time) and (session_time <= s["to"]):
                return s['ranges'], s['stepmode']

        sys.exit('Fail: time=%s not within any timezone in os=%s' % (session_time, schedules))

    @staticmethod
    def get_order_price(i, n_traders, ranges, mode):
        pmin = min(ranges[0]["min"], ranges[0]["max"])
        pmax = max(ranges[0]["min"], ranges[0]["max"])
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
                pmin = min(ranges[s]["min"], ranges[s]["max"])
                pmax = max(ranges[s]["min"], ranges[s]["max"])
            order_price = round(random.uniform(pmin, pmax), 0)
        else:
            sys.exit('FAIL: Unknown mode in schedule')

        return order_price

    def print_results(self):
        for tid in list(self.traders):
            t = self.traders[tid]
            print('%s N=%d B=%.2f' % (t.tid, t.n_trades, t.balance))

    def print_summary(self):
        meta_data = {}

        # COLLATE TRADERS BY TYPE
        for t in self.traders:
            t_type = self.traders[t].t_type

            if t_type in meta_data.keys():
                meta_data[t_type] = {
                    'n_trades': meta_data[t_type]['n_trades'] + 1,
                    'profit': meta_data[t_type]['profit'] + self.traders[t].balance
                }
            else:
                meta_data[t_type] = {'n_trades': 1, 'profit': self.traders[t].balance}

        # PRINT TRADER TYPE REPORT
        for t_type in sorted(list(meta_data.keys())):
            n = meta_data[t_type]['n_trades']
            profit = meta_data[t_type]['profit']
            print('%s, TOTAL=%.2f, AVERAGE=%.2f' % (t_type, profit, profit / float(n)))

        print('\n')

    def get_countdown(self):
        return (self.end_time - datetime.now()) / (self.end_time - self.start_time)

    def __sample_keys(self):
        random.shuffle(self.traders_keys)
        return self.traders_keys

    def place_order(self, lob):
        if datetime.now() < self.end_time:

            for t in self.__sample_keys():
                trader = self.traders[t]

                tradable_order = trader.get_order(self.get_countdown(), lob)
                if tradable_order is not None:
                    trader.place_order(tradable_order)

    def cancel_open_orders(self):
        for t in self.traders:
            self.traders[t].cancel_all_live()

    def run(self):

        def print_time():
            countdown = self.get_countdown()
            print("\nTime left {:.0%}  #############################################################".format(countdown))

        def distribute_new_order(t, t_id, n_traders, side, side_sched, session_time):
            ranges, mode = self.get_sched_mode(session_time, side_sched)
            price = self.get_order_price(t, n_traders, ranges, mode)

            self.traders[t_id].add_limit_order(self.create_limit_order(t_id, side, 1, price))

        def schedule_orders(side, side_trader_ids):
            now = datetime.now().replace(microsecond=0)

            side_sched = self.order_sched["demand"] if side == Side.BID else self.order_sched["supply"]

            # times in seconds i.e. 30.0
            issue_delays = self.get_issue_times(
                len(side_trader_ids),
                self.order_sched["timemode"],
                self.order_sched["interval"],
                True
            )

            print("Creating %s Schedule" % side)
            print(issue_delays)

            random.shuffle(side_trader_ids)
            random.shuffle(issue_delays)

            for t, t_id in enumerate(side_trader_ids):
                issue_time = now + timedelta(seconds=issue_delays[t])
                session_time = (issue_time - self.start_time).total_seconds()

                self.scheduler.add_job(
                    func=distribute_new_order,
                    name="Add Job Scheduler: " + side,
                    args=[t, t_id, len(side_trader_ids), side, side_sched, session_time],
                    trigger='date',
                    run_date=issue_time,
                )

        def end():
            print("\nEND OF MARKET SESSION")

            print("\nCANCELLING LIVE ORDERS")
            self.cancel_open_orders()

            print("\nREPORT")
            self.print_results()
            self.print_summary()

            print("APPLICATION SAFE TO CLOSE")

        self.scheduler.add_job(
            func=print_time,
            name="Time Scheduler",
            trigger='interval',
            seconds=5,
            start_date=self.start_time,
            end_date=self.end_time
        )

        # BUYERS
        self.scheduler.add_job(
            func=schedule_orders,
            name="BUY Scheduler",
            args=[
                Side.BID,
                list(self.buyers.keys()),
            ],
            trigger='interval',
            seconds=self.order_sched["interval"],
            start_date=self.start_time,
            end_date=self.end_time - timedelta(seconds=self.order_sched["interval"])
        )

        # SELLERS
        self.scheduler.add_job(
            func=schedule_orders,
            name="SELL Scheduler",
            args=[
                Side.ASK,
                list(self.sellers.keys())
            ],
            trigger='interval',
            seconds=self.order_sched["interval"],
            start_date=self.start_time,
            end_date=self.end_time - timedelta(seconds=self.order_sched["interval"])
        )

        self.scheduler.add_job(
            func=end,
            name="End Market Session",
            trigger='date',
            run_date=self.end_time
        )

        print("Open Market: Session %d" % self.trial_id)
        self.scheduler.start()

