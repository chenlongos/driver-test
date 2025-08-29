import pytest
import logging

class I2CTester:
    def __init__(self, debug_uart):
        self.debug_uart = debug_uart
        self.logger = logging.getLogger("I2C_Tester")
        self.test_result = False

    def run_i2c_test(self):
        """执行 I2C 初始化测试"""
        self.logger.info("开始 I2C 初始化测试...")
        response = self.debug_uart.send_command("i2c_init")
        self.test_result = "OK" in response
        self.logger.info(f"测试结果: {'PASSED' if self.test_result else 'FAILED'}")
        return self.test_result

@pytest.fixture(scope="module")
def i2c_tester(debug_uart):
    """I2C 测试 fixture"""
    tester = I2CTester(debug_uart)
    yield tester
    tester.logger.info("I2C 测试完成")

@pytest.mark.i2c
def test_i2c_initialization(i2c_tester):
    assert i2c_tester.run_i2c_test(), "I2C 初始化失败"