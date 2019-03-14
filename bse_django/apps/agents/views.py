from django.shortcuts import render

from bse_django.apps.agents.traders.Trader_Giveway import Trader_Giveaway
from bse_django.apps.agents.traders.Trader_Shaver import Trader_Shaver
from fix_application.FixClient import initialise_fix_app


def index(request):
    context = {}
    return render(request, 'agents/index.html', context)


def giveaway(request):
    tid = 0
    trader = Trader_Giveaway('GVWY', tid, 0.00)

    fix_app = initialise_fix_app("fix_application/client.cfg")
    fix_app.put_order()

    context = {
        'agent': {
            'name': 'GiveAway',
            'code': 'GVWY'
        }
    }
    return render(request, 'agents/agent.html', context)


def shaver(request):
    tid = 0
    trader = Trader_Shaver('SHVR', tid, 0.00)

    fix_app.put_order()

    context = {
        'agent': {
            'name': 'Shaver',
            'code': 'SHVR'
        }
    }
    return render(request, 'agents/agent.html', context)

