"""This module is main module for contestant's solution."""

from hackathon.utils.control import Control
from hackathon.utils.utils import ResultsMessage, DataMessage, PVMode, \
    TYPHOON_DIR, config_outs
from hackathon.framework.http_server import prepare_dot_dir


def worker(msg: DataMessage) -> ResultsMessage:
    load_one = True
    load_two = True
    load_three = True
    power_reference = 0.0
    pv_mode = PVMode.ON

    # if overload baterije u minimum, gasi bojler
    if msg.bessSOC < 0.1:
        load_three = False

    # if overload baterije u maximum, prodaj struju ako je povoljno inače pali bojler
    # if 30% bojlera skuplje od 0.1, gasi bojler inače upali
    # if nema mrežne struje, gasi bojler
    # if baterija ispod X kWh, gasi bojler
    # ako je penal bojlera manji od prodajne cene, gasi bojler i prodaj višak ili puni bateriju
    # ako puno raste PV, biće puno energije
    return ResultsMessage(data_msg=msg,
                          load_one=load_one,
                          load_two=load_two,
                          load_three=load_three,
                          power_reference=power_reference,
                          pv_mode=pv_mode)


def run(args) -> None:
    prepare_dot_dir()
    config_outs(args, 'solution')

    cntrl = Control()

    for data in cntrl.get_data():
        cntrl.push_results(worker(data))
