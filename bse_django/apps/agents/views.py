from django.shortcuts import render

from fix_application.traders.Trader_Giveaway import Trader_Giveaway
from fix_application.traders.Trader_Shaver import Trader_Shaver


def index(request):
    context = {}
    return render(request, 'agents/index.html', context)

def giveaway(request):
    tid = 0
    trader = Trader_Giveaway('GVWY', tid, 0.00)

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

    context = {
        'agent': {
            'name': 'Shaver',
            'code': 'SHVR'
        }
    }
    return render(request, 'agents/agent.html', context)

