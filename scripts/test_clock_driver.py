import pytest
import logging

class Clock_Tester:
    def __init__(self, debug_uart):
        self.logger = logging.getLogger('Clock_Tester')
        self.test_result = False 
        self.debug_uart = debug_uart

    def run_clock_test(self):
        self.logger.info("Sending clock_test command")
        response = self.debug_uart.send_command("clock_init")
        self.test_result = "OK" in response
        assert self.test_result, "Clock driver test failed"

    def run_clock_functionality_test(self, freq):
        self.logger.info("Sending clock_test command")
        response = self.debug_uart.send_command(f"clock_test {freq}")
        self.test_result = "OK" in response
        assert self.test_result, f"Clock driver functionality test failed at {freq} Hz"

@pytest.fixture(scope="module")
def clock_tester(debug_uart):
    """Clock 测试 fixture"""
    tester = Clock_Tester(debug_uart)
    yield tester
    tester.logger.info("Clock 测试完成")

@pytest.mark.clock
def test_clock_initialization(clock_tester):
    assert clock_tester.run_clock_test(), "Clock driver test failed"

@pytest.mark.clock
def test_clock_functionality(clock_tester):
    assert clock_tester.run_clock_functionality_test(1000000), "Clock driver functionality test failed at 1000000 Hz"

