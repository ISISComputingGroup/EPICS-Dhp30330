from lewis.adapters.stream import StreamInterface
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
            CmdBuilder(self.get_current).escape("MEAS:CURR?").eos().build(),
            CmdBuilder(self.get_current_sp).escape("SOUR:CURR?").eos().build(),
            CmdBuilder(self.get_voltage).escape("MEAS:VOLT?").eos().build(),
            CmdBuilder(self.get_voltage_sp).escape("SOUR:VOLT?").eos().build(),
            CmdBuilder(self.get_power).escape("MEAS:POW?").eos().build(),
            CmdBuilder(self.get_power_sp).escape("SOUR:POW?").eos().build(),
            CmdBuilder(self.get_status).escape("DIAG:DISP:IND?").build(),
            CmdBuilder(self.set_current_sp).escape("SOUR:CURR").spaces(at_least_one=True).float().eos().build(),
            CmdBuilder(self.set_voltage_sp).escape("SOUR:VOLT").spaces(at_least_one=True).float().eos().build(),
            CmdBuilder(self.set_power_sp).escape("SOUR:POW").spaces(at_least_one=True).float().eos().build()
        }

    def handle_error(self, request, error):
        """
        If command is not recognised print and error

        Args:
            request: requested string
            error: problem

        """
        self.log.error("An error occurred at request " + repr(request) + ": " + repr(error))

    @conditional_reply("connected")
    def get_current(self):
        return f"{self.device.current}"
    
    @conditional_reply("connected")
    def get_current_sp(self):
        return f"{self.device.current_sp}"

    @conditional_reply("connected")
    def get_voltage(self):
        return f"{self.device.voltage}"
    
    @conditional_reply("connected")
    def get_voltage_sp(self):
        return f"{self.device.voltage_sp}"

    @conditional_reply("connected")
    def get_power(self):
        return f"{self.device.power}"
    
    @conditional_reply("connected")
    def get_power_sp(self):
        return f"{self.device.power_sp}"

    @conditional_reply("connected")
    def get_status(self):
        return f"{self.device.constant_voltage},{self.device.constant_current},{self.device.constant_power},{self.device.remote}"

    @conditional_reply("connected")
    def set_current_sp(self, value):
        self.device.current = value
        self.device.current_sp = value
        return ""

    @conditional_reply("connected")
    def set_voltage_sp(self, value):
        self.device.voltage = value
        self.device.voltage_sp = value
        return ""

    @conditional_reply("connected")
    def set_power_sp(self, value):
        self.device.power_sp = value
        return ""
