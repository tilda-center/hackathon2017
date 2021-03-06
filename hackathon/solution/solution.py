"""This module is main module for contestant's solution."""

from hackathon.utils.control import Control
from hackathon.utils.utils import ResultsMessage, DataMessage, PVMode, \
    TYPHOON_DIR, config_outs
from hackathon.framework.http_server import prepare_dot_dir


min_battery_threshold = 0.3
max_battery_threshold = 0.5
blackout_end_iteration = 8000


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
                if msg.buying_price / 60.0 >= 0.1: # više se isplati gasiti load3 nego kupovati
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


def guess_blackouts(msg):
    global min_battery_threshold
    global max_battery_threshold
    global blackout_end_iteration

    day_iterator = int(msg.id / 60 / 24)
    if msg.grid_status == 0:
        min_battery_threshold = 0.5
        max_battery_threshold = 0.6
        blackout_end_iteration = msg.id
    elif blackout_end_iteration < msg.id and msg.id < blackout_end_iteration + 8 * 60:
        min_battery_threshold = 0.0
        max_battery_threshold = 0.1
    elif msg.id > 7200 - 80:
        min_battery_threshold = 0.0
        max_battery_threshold = 0.1
    else:
        min_battery_threshold = 0.1
        max_battery_threshold = 0.5


def stedi(msg):
    load_one = True
    load_two = True
    load_three = True
    power_reference = 0.0
    pv_mode = PVMode.ON

    extra_production = msg.solar_production - msg.current_load
    if msg.grid_status: # radi elektrovojvodina
        if msg.buying_price / 60.0 > 0.1: # više se isplati gasiti load3 nego puniti iz elektrovojvodine
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

    extra_production = msg.solar_production - msg.current_load
    if msg.grid_status: # radi elektrovojvodina
        if msg.bessSOC < min_battery_threshold: #posto imamo mrezu, stedimo bateriju maksimalno
            if msg.buying_price / 60.0 > 0.1: #skupa struja, gasi load3
                load_three = False
                power_reference = -1.0
            else:
                power_reference = -3.0 #struja je jeftina pa maksimalno punimo bateriju
        elif msg.bessSOC < max_battery_threshold: # baterija je ispod threshold
            if extra_production > 0: # panel može da puni bateriju
                if extra_production > 6.0: # panel daje više nego što baterija može da primi
                    power_reference = -6.0
                else: # panel daje najviše onoliko koliko baterija može da primi
                    power_reference = -extra_production
            else:
                if msg.buying_price / 60.0 >= 0.1: # više se isplati gasiti load3 nego kupovati
                    load_three = False
                    current_load = msg.current_load * 0.7
                    new_extra_production = msg.solar_production - current_load
                    if new_extra_production > 0: # sa isključenim load3 ima dosta struje
                        power_reference = -extra_production
                else: # više se isplati kupovati struju nego gasiti load3
                    if msg.buying_price / 60 < 0.1:
                        power_reference = -1.0
        else: # baterija nije kritično prazna
            if extra_production > 0: # panel može da puni bateriju
                if extra_production > 6.0: # panel daje više nego što baterija može da primi
                    power_reference = -6.0
                else: # panel daje najviše onoliko koliko baterija može da primi
                    power_reference = -extra_production
            else: # panel nema dovoljno energije da zadovolji load
                if msg.buying_price / 60.0 >= 0.1: #struja je skupa
                    load_three = False
                    current_load = msg.current_load * 0.7
                    new_extra_production = msg.solar_production - current_load
                    if new_extra_production < -6.0 :
                        power_reference = 6.0 #ostalo kupuje iz elektrane
                    else:
                        power_reference = -new_extra_production #napaja ga samo baterija

                else:#jeftina je struja i vucemo iz elektrane
                    if extra_production < -1.0:
                        power_reference = 1.0 #ostalo kupuje iz elektrane

    else: # ne radi elektrovojvodina
        all_energy = msg.solar_production + 6.0
        extra_production = all_energy - msg.current_load
        if extra_production < 0: # nema dovoljno sunca
            power_reference = -extra_production
            if msg.current_load * 0.2 > all_energy: # čak i sa samo load1 trošimo previše pa isključi sve
                load_one = False
                load_two = False
                load_three = False
            elif msg.current_load * 0.5 > all_energy: # isključenjem load2 trošimo previše
                load_two = False
                load_three = False
            elif msg.current_load * 0.7 <= all_energy: # dovoljno je isključiti samo load3
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



def worker(msg: DataMessage) -> ResultsMessage:
    result = None
    guess_blackouts(msg)
    # overload baterije
    if msg.bessOverload:
        # maximum
        if msg.bessSOC == 1:
            result = potrosi(msg)
        else:
            result = stedi(msg)
    else: # sve normalno radi
        result = potrosiIliProdaj(msg)


    # ako puno raste PV, biće puno energije
    return result


def run(args) -> None:
    prepare_dot_dir()
    config_outs(args, 'solution')

    cntrl = Control()
    #pozovi generate_profiles()
    #exploit
    #obrisi fajl data/profiles.json

    for data in cntrl.get_data():
        cntrl.push_results(worker(data))
