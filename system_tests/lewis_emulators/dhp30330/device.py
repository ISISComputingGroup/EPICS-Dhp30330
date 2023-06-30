from lewis.core.logging import has_log
from lewis.devices import StateMachineDevice

@has_log
class Simulateddhp30330(StateMachineDevice):
    """
    Simulated dhp30330 Power Supply
    """
    def _initalize_data(self):
        self.current = 0
        self.volt = 0
        self. power = 0


