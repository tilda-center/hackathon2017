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

    extra_production = msg.solar_production - msg.current_load
    if msg.grid_status: # radi elektrovojvodina
        if extra_production < 0: # pravim manje energije od max load
            if msg.solar_production + 6.0 < msg.current_load: # panel i baterija prave manje energije od max load
                power_reference = 6.0
                if msg.buying_price / 60 >= 0.1: # više se isplati gasiti load3 nego kupovati
                    load_three = False
            else: # panel i baterija mogu da prave makar max load
                if extra_production < -6.0:
                    power_reference = 6.0
                else:
                    power_reference = -extra_production
        else: # pravim barem energije od max load
            power_reference = 0.1
    else: # ne radi elektrovojvodina
        if extra_production >= 0: # pravim iz panela barem max load
            pv_mode = PVMode.OFF
            if msg.current_load * 0.7 >= 6.0: # isklučenje load3 nije dovoljno
                load_two = False
            else: # isključenje load3 je dovoljno
                load_three = False
        else: # pravim iz panela manje od max load
            if msg.solar_production + 6.0 <= msg.current_load: # panel i baterija ne prave dovoljno
                current_load = msg.current_load * 0.7
                if msg.solar_production + 6.0 < current_load: # panel i baterija prave manje od load1 + load2
                    load_two = False # tloken
                else: # panel i baterija prave barem load1 + load2
                    load_three = False

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

    extra_production = msg.solar_production - msg.current_load
    if msg.grid_status: # radi elektrovojvodina
        if msg.buying_price / 60 > 0.1: # više se isplati gasiti load3 nego puniti iz elektrovojvodine
            load_three = False
            power_reference = -0.1
    else: # ne radi elektrovojvodina
        if extra_production <= 0: # nema dovoljno sunca
            if msg.current_load * 0.2 > msg.solar_production: # čak i sa samo load1 trošimo previše pa isključi sve
                load_one = False
                load_two = False
                load_three = False
            elif msg.current_load * 0.5 > msg.solar_production: # isključenjem load2 trošimo previše
                load_two = False
                load_three = False
            elif msg.current_load * 0.7 < msg.solar_production: # dovoljno je isključiti samo load3
                load_three = False
            else: # dovoljno je isključiti samo load2
                load_two = False


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
