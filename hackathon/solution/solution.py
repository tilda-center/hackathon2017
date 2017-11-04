"""This module is main module for contestant's solution."""

from hackathon.utils.control import Control
from hackathon.utils.utils import ResultsMessage, DataMessage, PVMode, \
    TYPHOON_DIR, config_outs
from hackathon.framework.http_server import prepare_dot_dir


def potrosi(msg):
    load_one = True
    load_two = True
    load_three = True
    power_reference = 0.0
    pv_mode = PVMode.ON
    result = ResultsMessage(
        data_msg=msg,
        load_one=load_one,
        load_two=load_two,
        load_three=load_three,
        power_reference=power_reference,
        pv_mode=pv_mode,
    )
    return result


def stedi(msg):
    load_one = True
    load_two = True
    load_three = True
    power_reference = 0.0
    pv_mode = PVMode.ON
    result = ResultsMessage(
        data_msg=msg,
        load_one=load_one,
        load_two=load_two,
        load_three=load_three,
        power_reference=power_reference,
        pv_mode=pv_mode,
    )
    return result


def potrosiIliProdaj(msg):
    load_one = True
    load_two = True
    load_three = True
    power_reference = 0.0
    pv_mode = PVMode.ON
    result = ResultsMessage(
        data_msg=msg,
        load_one=load_one,
        load_two=load_two,
        load_three=load_three,
        power_reference=power_reference,
        pv_mode=pv_mode,
    )
    return result


def worker(msg: DataMessage) -> ResultsMessage:
    result = None
    # overload baterije
    if msg.bessOverload:
        # maximum
        if msg.bessSOC == 1:
            result = potrosi(msg)
        else:
            result = stedi(msg)
    elif not msg.grid_status:
        result = stedi(msg)
    else: # sve normalno radi
        result = potrosiIliProdaj(msg)


    # ako puno raste PV, biće puno energije
    return result


def run(args) -> None:
    prepare_dot_dir()
    config_outs(args, 'solution')

    cntrl = Control()

    for data in cntrl.get_data():
        cntrl.push_results(worker(data))
