from collections import OrderedDict
from .states import DefaultState
from lewis.devices import StateMachineDevice


class SimulatedDhp30330(StateMachineDevice):

    def _initialize_data(self):
        """
        Initialize all of the device's attributes.
        """
        self.reset()

    def _get_state_handlers(self):
        return { "default": DefaultState() }

    def _get_initial_state(self):
        return "default"

    def _get_transition_handlers(self):
        return OrderedDict([])

    def reset(self):
        self.connected = True

        self.current = 0
        self.voltage = 0.0
        self.power = 0
        self.current_sp = 0
        self.voltage_sp = 0.0
        self.power_sp = 0
        self.constant_voltage = 0 # First status character.
        self.constant_current = 0 # Second status character.
        self.constant_power = 0   # Third status character.
        self.remote = 0           # Fourth status character.
