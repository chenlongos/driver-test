import pytest
import logging

class GPIOTester:
    def __init__(self, debug_uart):
        self.debug_uart = debug_uart  # 接收全局 debug_uart 实例
        self.logger = logging.getLogger("GPIO_Tester")
        self.test_result = False

    def run_gpio_test(self):
        """执行 GPIO 初始化测试"""
        self.logger.info("开始 GPIO 初始化测试...")
        response = self.debug_uart.send_command("gpio_init")
        self.test_result = "OK" in response
        self.logger.info(f"测试结果: {'PASSED' if self.test_result else 'FAILED'}")
        return self.test_result

    def run_gpio_functional_test(self):
        """执行 GPIO 功能测试"""
        self.logger.info("开始 GPIO 功能测试...")
        response = self.debug_uart.send_command("gpio_test")
        self.test_result = "OK" in response
        self.logger.info(f"测试结果: {'PASSED' if self.test_result else 'FAILED'}")
        return self.test_result

@pytest.fixture(scope="module")
def gpio_tester(debug_uart):
    """GPIO 测试 fixture，依赖全局 debug_uart"""
    tester = GPIOTester(debug_uart)
    yield tester
    tester.logger.info("GPIO 测试完成")

@pytest.mark.gpio
def test_gpio_initialization(gpio_tester):
    assert gpio_tester.run_gpio_test(), "GPIO 初始化失败"

@pytest.mark.gpio
def test_gpio_functionality(gpio_tester):
    assert gpio_tester.run_gpio_functional_test(), "GPIO 功能测试失败"