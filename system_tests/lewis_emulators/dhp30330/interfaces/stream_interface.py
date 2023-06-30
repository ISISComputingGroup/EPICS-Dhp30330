import traceback

from lewis.adapters.stream import StreamInterface
from lewis.utils.command_builder import CmdBuilder
from lewis.core.logging import has_log


@has_log
class DHP30330StreamInterface(StreamInterface):
    in_terminator = "\r"
    out_terminator = "\r"
    commands = {
        CmdBuilder("get_idn").escape("*IDN?").eos().build(),
        CmdBuilder("get_current").escape("MEAS:CURR?").eos().build(),
        CmdBuilder("get_current_limit").escape("SOUR:CURR?").eos().build(),
        CmdBuilder("get_voltage").escape("MEAS:VOLT?").eos().build(),
        CmdBuilder("get_voltage_limit").escape("SOUR:VOLT?").eos().build(),
        CmdBuilder("get_power").escape("MEAS:POW?").eos().build(),
        CmdBuilder("get_power_limit").escape("SOUR:POW?").eos().build(),
        CmdBuilder("get_constants").escape("DIAG:DISP:IND?").build()
    }

    def get_idn(self):
        return self._device.idn

    def get_current(self):
        return str(self._device.current)

    def get_voltage(self):
        return str(self._device.voltage)

    def get_power(self):
        return str(self._device.power)

    def get_current_limit(self):
        return str(self._device.current_limit)

    def get_voltage_limit(self):
        return str(self._device.voltage_limit)

    def get_power_limit(self):
        return str(self._device.power_limit)

    def get_constants(self):
        return f"{self._device.current_bool}{self._device.voltage_bool}" \
               f"{self._device.power_bool},{self._device.remote}"
