import time
import unittest

from parameterized import parameterized
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, ProcServLauncher, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, parameterized_list, skip_if_recsim

DEVICE_PREFIX = "DHP30330_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("DHP30330"),
        "ioc_launcher_class": ProcServLauncher,
        "macros": {},
        "emulator": "dhp30330",
    },
]


TEST_MODES = [TestModes.DEVSIM]


DEVICE_VARIABLES = {
    "CURR": "current",
    "VOLT": "voltage",
    "POW": "power",
    "CONST:VOLT": "constant_voltage",
    "CONST:CURR": "constant_current",
    "CONST:POW": "constant_power",
    "REMOTE": "remote",
}


class Dhp30330Tests(unittest.TestCase):
    """
    Tests for the Dhp30330 IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("dhp30330", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_wait_time=0)
        self._reset_device()

    def _reset_device(self):
        if IOCRegister.uses_rec_sim:
            self.ca.set_pv_value("SIM:CURR", 0)
            self.ca.set_pv_value("SIM:CURR:SP", 0)
            self.ca.set_pv_value("SIM:VOLT", 0.0)
            self.ca.set_pv_value("SIM:VOLT:SP", 0.0)
            self.ca.set_pv_value("SIM:POW", 0)
            self.ca.set_pv_value("SIM:POW:SP", 0)
            self.ca.set_pv_value("SIM:CONST:VOLT", 0)
            self.ca.set_pv_value("SIM:CONST:CURR", 0)
            self.ca.set_pv_value("SIM:CONST:POW", 0)
            self.ca.set_pv_value("SIM:CONST:POW:SP", 0)
            self.ca.set_pv_value("SIM:REMOTE", 0)
        else:
            self._lewis.backdoor_run_function_on_device("reset")

        self.ca.set_pv_value("CONST:POW:SP", 0)

        time.sleep(5)  # Wait for all periodic scan PVs to process.

    def _set(self, pv, value):
        if IOCRegister.uses_rec_sim:
            self.ca.set_pv_value(f"SIM:{pv}", value)
        else:
            self._lewis.backdoor_set_on_device(DEVICE_VARIABLES[pv], value)

    @parameterized.expand(
        parameterized_list(
            [
                ("CURR", 120, 120),
                ("VOLT", 12.5, 12.5),
                ("POW", 535, 535),
                ("CONST:VOLT", 1, "YES"),
                ("CONST:CURR", 1, "YES"),
                ("CONST:POW", 1, "YES"),
                ("REMOTE", 1, "YES"),
            ]
        )
    )
    def test_WHEN_read_only_pv_set_THEN_pv_read_correctly(self, _, pv, set_value, expected_value):
        self._set(pv, set_value)
        self.ca.assert_that_pv_is(pv, expected_value)

    @parameterized.expand(
        parameterized_list(
            [
                ("CURR:SP:RBV", "CURR:SP", 77),
                ("VOLT:SP:RBV", "VOLT:SP", 6.3),
                ("POW:SP:RBV", "POW:SP", 333),
            ]
        )
    )
    def test_WHEN_limit_set_THEN_limit_correct(self, _, pv, sp, value):
        self.ca.set_pv_value(sp, value)
        self.ca.assert_that_pv_is(pv, value)

    @skip_if_recsim("Requires emulator for disconnect logic.")
    def test_WHEN_device_disconnects_THEN_pvs_go_into_alarm(self):
        self.ca.assert_that_pv_alarm_is("CURR", self.ca.Alarms.NONE)

        with self._lewis.backdoor_simulate_disconnected_device():
            self.ca.assert_that_pv_alarm_is("CURR", self.ca.Alarms.INVALID, timeout=30)

        self.ca.assert_that_pv_alarm_is("CURR", self.ca.Alarms.NONE, timeout=30)

    def test_GIVEN_known_power_WHEN_calculated_power_read_THEN_value_correct(self):
        current = 120
        voltage = 3.3
        power = current * voltage

        self._set("CURR", current)
        self._set("VOLT", voltage)

        self.ca.assert_that_pv_is("POW:CALC", power)

    def test_GIVEN_known_resistance_WHEN_calculated_resistance_read_THEN_value_correct(self):
        voltage = 5.1
        current = 12
        resistance = voltage / current

        self._set("VOLT", voltage)
        self._set("CURR", current)

        self.ca.assert_that_pv_is("RES:CALC", resistance)

    @parameterized.expand(
        parameterized_list(
            [
                (10, 10 * 1.5),  # Within limit (below).
                (10, 10 * 0.8),  # Within limit (above).
            ]
        )
    )
    def test_WHEN_no_stop_condition_THEN_stop_pv_is_not_processed(self, _, first, second):
        self.ca.set_pv_value("CURR:SP", first, wait=True)
        self.ca.set_pv_value("VOLT:SP", first, wait=True)

        self._set("CURR", first)
        self._set("VOLT", first)

        time.sleep(5)  # Wait for all periodic scan PVs to process.

        with self.ca.assert_pv_not_processed("STOP"):
            self._set("CURR", second)
            self._set("VOLT", second)

            time.sleep(5)  # Wait for all periodic scan PVs to process.

        self.ca.assert_that_pv_is("CURR:SP:RBV", first)
        self.ca.assert_that_pv_is("VOLT:SP:RBV", first)

    @parameterized.expand(
        parameterized_list(
            [
                (2, 2 * 2.5, 2, 2 * 2.5),  # Both overlimit.
                (2, 2 * 0.2, 2, 2 * 0.2),  # Both underlimit.
                (2, 2 * 0.2, 2, 2 * 1.5),  # Current underlimit, voltage normal.
                (2, 2 * 2.5, 2, 2 * 1.5),  # Current overlimit, voltage normal.
                (2, 2 * 1.5, 2, 2 * 0.2),  # Current normal, voltage underlimit.
                (2, 2 * 1.5, 2, 2 * 2.5),  # Current normal, voltage overlimit.
            ]
        )
    )
    def test_WHEN_stop_condition_triggered_THEN_all_set_to_zero(
        self, _, curr_first, curr_second, volt_first, volt_second
    ):
        self.ca.set_pv_value("CURR:SP", curr_first)
        self.ca.set_pv_value("VOLT:SP", volt_first)

        self._set("CURR", curr_first)
        self._set("VOLT", volt_first)

        time.sleep(5)  # Wait for all periodic scan PVs to process.

        self._set("CURR", curr_second)
        self._set("VOLT", volt_second)

        time.sleep(5)  # Wait for all periodic scan PVs to process.

        self.ca.assert_that_pv_is("CURR:SP:RBV", 0)
        self.ca.assert_that_pv_is("VOLT:SP:RBV", 0)

    def test_GIVEN_default_macros_set_WHEN_limits_read_THEN_limits_correct(self):
        current = 120
        voltage = 5.2
        power = 650
        macros = {
            "DEFAULT_CURR_LIMIT": current,
            "DEFAULT_VOLT_LIMIT": voltage,
            "DEFAULT_POW_LIMIT": power,
        }

        with self._ioc.start_with_macros(macros, pv_to_wait_for="CURR"):
            self.ca.assert_that_pv_is("CURR:SP:RBV", current)
            self.ca.assert_that_pv_is("VOLT:SP:RBV", voltage)
            self.ca.assert_that_pv_is("POW:SP:RBV", power)

    @parameterized.expand(
        parameterized_list(
            [
                (0, 0, 30, 60, 0.5, 50),  # Power needs adjusting up from 0
                (30, 0.5, 0, 30, 0, 20),  # Power needs adjusting down to 0
                (100, 4.4, 650, 140, 4.7, 690),  # Power needs adjusting up
                (120, 5.4, 600, 120, 5.1, 640),  # Power needs adjusting down
            ]
        )
    )
    def test_GIVEN_const_power_mode_on_WHEN_calculated_power_out_of_range_THEN_voltage_and_current_adjusted(
        self,
        _,
        curr,
        volt,
        power_limit,
        expected_curr_limit,
        expected_volt_limit,
        expected_power_limit,
    ):
        self.ca.set_pv_value("CURR:REQ:SP", curr)
        self.ca.set_pv_value("VOLT:REQ:SP", volt)
        self._set("CURR", curr)
        self._set("VOLT", volt)

        self.ca.set_pv_value("POW:REQ:SP", power_limit)

        time.sleep(2)

        self.ca.set_pv_value("CONST:POW:SP", 1)

        timeout = 20
        self.ca.assert_that_pv_is("CURR:SP:RBV", expected_curr_limit, timeout=timeout)
        self.ca.assert_that_pv_is("VOLT:SP:RBV", expected_volt_limit, timeout=timeout)
        self.ca.assert_that_pv_is("POW:SP:RBV", expected_power_limit, timeout=timeout)
        self.ca.assert_that_pv_is("POW:WITHIN:TOLERANCE", 1, timeout=timeout)

    def test_GIVEN_const_power_mode_off_WHEN_calculated_power_out_of_range_THEN_voltage_and_current_not_adjusted(
        self,
    ):
        curr = 120
        volt = 3.0

        self.ca.set_pv_value("CURR:REQ:SP", curr)
        self.ca.set_pv_value("VOLT:REQ:SP", volt)

        with self.ca.assert_pv_not_processed("ADJUST"):
            self._set("CURR", curr)
            self._set("VOLT", volt)

            time.sleep(5)  # Wait for all periodic scan PVs to process.

        self.ca.assert_that_pv_is("CURR", curr)
        self.ca.assert_that_pv_is("VOLT", volt)
        self.ca.assert_that_pv_is("POW:WITHIN:TOLERANCE", 0)
