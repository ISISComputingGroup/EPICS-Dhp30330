from lewis.adapters.stream import StreamInterface, Cmd
from lewis.utils.command_builder import CmdBuilder
from lewis.core.logging import has_log
from lewis.utils.replies import conditional_reply


@has_log
class Dhp30330StreamInterface(StreamInterface):
    
    in_terminator = "\r"
    out_terminator = "\r"

    def __init__(self):
        super(Dhp30330StreamInterface, self).__init__()
        # Commands that we expect via serial during normal operation
        self.commands = {
            CmdBuilder("get_idn").escape("*IDN?").eos().build(),
            CmdBuilder("get_current").escape("MEAS:CURR?").eos().build(),
            CmdBuilder("get_current_limit").escape("SOUR:CURR?").eos().build(),
            CmdBuilder("get_voltage").escape("MEAS:VOLT?").eos().build(),
            CmdBuilder("get_voltage_limit").escape("SOUR:VOLT?").eos().build(),
            CmdBuilder("get_power").escape("MEAS:POW?").eos().build(),
            CmdBuilder("get_power_limit").escape("SOUR:POW?").eos().build(),
            CmdBuilder("get_constants").escape("DIAG:DISP:IND?").build()
        }

    def handle_error(self, request, error):
        """
        If command is not recognised print and error

        Args:
            request: requested string
            error: problem

        """
        self.log.error("An error occurred at request " + repr(request) + ": " + repr(error))

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
