import pytest
import logging

class CRUTester:
    def __init__(self, debug_uart):
        self.debug_uart = debug_uart
        self.logger = logging.getLogger("CRU_Tester")
        self.test_result = False

    def run_cru_test(self):
        """执行 CRU 测试"""
        self.logger.info("开始 CRU 测试...")
        response = self.debug_uart.send_command("cru_init")
        self.test_result = "OK" in response
        self.logger.info(f"测试结果: {'PASSED' if self.test_result else 'FAILED'}")
        return self.test_result
    
    def run_cru_functional_test(self):
        """执行 CRU 功能测试"""
        self.logger.info("开始 CRU 功能测试...")
        response = self.debug_uart.send_command("cru_test")
        self.test_result = "OK" in response
        self.logger.info(f"测试结果: {'PASSED' if self.test_result else 'FAILED'}")
        return self.test_result
    
@pytest.fixture(scope="module")
def cru_tester(debug_uart):
    """CRU 测试 fixture"""
    tester = CRUTester(debug_uart)
    yield tester
    tester.logger.info("CRU 测试完成")

@pytest.mark.reset
def test_cru_initialization(cru_tester):
    assert cru_tester.run_cru_test(), "CRU 初始化失败"

