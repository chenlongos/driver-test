import pytest
import logging
import time

class WatchdogTester:
    def __init__(self, debug_uart):
        self.debug_uart = debug_uart
        self.logger = logging.getLogger("Watchdog_Tester")
        self.test_result = False

    def run_watchdog_test(self):
        """执行 Watchdog 初始化测试"""
        self.logger.info("开始 Watchdog 初始化测试...")
        response = self.debug_uart.send_command("watchdog_init")
        self.test_result = "OK" in response
        self.logger.info(f"测试结果: {'PASSED' if self.test_result else 'FAILED'}")
        return self.test_result

    def run_watchdog_functional_test(self):
        """执行 Watchdog 功能测试"""
        self.logger.info("开始 Watchdog 功能测试...")
        response = self.debug_uart.send_command("watchdog_test")
        self.test_result = "OK" in response
        self.logger.info(f"测试结果: {'PASSED' if self.test_result else 'FAILED'}")
        time.sleep(10)
        return self.test_result

@pytest.fixture(scope="module")
def watchdog_tester(debug_uart):
    """Watchdog 测试 fixture"""
    tester = WatchdogTester(debug_uart)
    yield tester
    tester.logger.info("Watchdog 测试完成")

@pytest.mark.watchdog
def test_watchdog_initialization(watchdog_tester):
    assert watchdog_tester.run_watchdog_test(), "Watchdog 初始化失败"

@pytest.mark.watchdog
@pytest.mark.reset
def test_watchdog_functionality(watchdog_tester):
    assert watchdog_tester.run_watchdog_functional_test(), "Watchdog 功能测试失败"