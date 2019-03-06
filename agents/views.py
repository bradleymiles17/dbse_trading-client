import requests

from django.shortcuts import render
from django.http import HttpResponse

from agents.traders.Trader_Giveway import Trader_Giveaway
from agents.traders.Trader_Shaver import Trader_Shaver


def index(request):
    context = {}
    return render(request, 'agents/index.html', context)


def giveaway(request):
    tid = 0
    trader = Trader_Giveaway('GVWY', tid, 0.00)

    # connect to exchange - get lob
    response = requests.get("http://127.0.0.1:5000/api/lob")

    context = {
        'agent': {
            'name': 'GiveAway',
            'code': 'GVWY'
        },
        'lob': response.content
    }
    return render(request, 'agents/agent.html', context)


def shaver(request):
    tid = 0
    trader = Trader_Shaver('SHVR', tid, 0.00)

    # connect to exchange - get lob
    response = requests.get("http://127.0.0.1:5000/api/lob")

    context = {
        'agent': {
            'name': 'Shaver',
            'code': 'SHVR'
        },
        'lob': response.content
    }
    return render(request, 'agents/agent.html', context)

