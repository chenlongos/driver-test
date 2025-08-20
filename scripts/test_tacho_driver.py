import pytest
import logging

class TachoTester:
    def __init__(self, debug_uart):
        self.debug_uart = debug_uart
        self.logger = logging.getLogger("Tacho_Tester")
        self.test_result = False

    def run_tacho_test(self):
        """执行 Tacho 初始化测试"""
        self.logger.info("开始 Tacho 初始化测试...")
        response = self.debug_uart.send_command("tacho_init")
        self.test_result = "OK" in response
        self.logger.info(f"测试结果: {'PASSED' if self.test_result else 'FAILED'}")
        return self.test_result

@pytest.fixture(scope="module")
def tacho_tester(debug_uart):
    """Tacho 测试 fixture"""
    tester = TachoTester(debug_uart)
    yield tester
    tester.logger.info("Tacho 测试完成")

@pytest.mark.tacho
def test_tacho_initialization(tacho_tester):
    assert tacho_tester.run_tacho_test(), "Tacho 初始化失败"