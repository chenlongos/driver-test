import pytest
import serial
import random
import string
import time
import logging
from typing import List, Dict, Tuple

# 测试配置
DEBUG_UART_PORT = "/dev/ttyUSB0"  # 调试串口，波特率固定
TEST_UART_PORT = "/dev/ttyUSB1"   # 被测串口，波特率可设置
DEBUG_BAUDRATE = 115200            # 调试串口固定波特率
DEFAULT_BAUDRATE = 115200          # 被测串口默认波特率
TEST_BAUDRATES = [9600, 19200, 38400, 57600, 230400]
TEST_CHAR_COUNT = 10
STOP_CHAR = b'\x00'  # 停止发送的字符

class DebugUART:
    """调试串口管理器，保持长期连接"""
    _instance = None
    
    def __new__(cls, port: str, baudrate: int):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.port = port
            cls._instance.baudrate = baudrate
            cls._instance.ser = None
        return cls._instance
    
    def connect(self) -> bool:
        """建立调试串口连接"""
        if self.ser and self.ser.is_open:
            return True
        
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=2,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            return self.ser.is_open
        except Exception as e:
            print(f"调试串口连接失败: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """断开调试串口连接"""
        if self.ser and self.ser.is_open:
            self.ser.close()
    
    def send_command(self, command: str) -> bool:
        """发送命令到开发板"""
        if not self.ser or not self.ser.is_open:
            return False
        
        try:
            self.ser.write(f"{command}\r\n".encode())
            time.sleep(0.5)  # 等待命令执行
            return True
        except Exception as e:
            print(f"发送命令失败: {str(e)}")
            return False


class UART_Tester:
    def __init__(self, test_port: str, test_baudrate: int = DEFAULT_BAUDRATE):
        self.test_port = test_port
        self.test_baudrate = test_baudrate
        self.test_ser = None
        self.debug_uart = DebugUART(DEBUG_UART_PORT, DEBUG_BAUDRATE)
        self.test_results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "details": []
        }
        self.logger = logging.getLogger('UART_Tester')

    
    def connect_test_port(self) -> bool:
        """仅连接被测串口"""
        if self.test_ser and self.test_ser.is_open:
            return True
        
        try:
            self.logger.info(f"正在连接被测串口: {self.test_port}")
            # 连接被测串口
            self.test_ser = serial.Serial(
                port=self.test_port,
                baudrate=self.test_baudrate,
                timeout=0.1,  # 短超时用于逐字符接收
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            self.logger.info(f"成功连接被测串口: {self.test_port}")
            return self.test_ser.is_open
        except Exception as e:
            self.logger.error(f"连接被测串口失败: {str(e)}")
            self.disconnect_test_port()
            return False
    
    def disconnect_test_port(self) -> None:
        """仅断开被测串口连接"""
        if self.test_ser and self.test_ser.is_open:
            self.test_ser.close()
            self.test_ser = None
    
    def send_command(self, command: str) -> bool:
        """通过调试串口发送命令到开发板"""
        return self.debug_uart.send_command(command)
    
    def set_baudrate(self, baudrate: int) -> bool:
        """通过调试串口发送波特率设置命令，然后配置被测串口"""
        self.logger.info(f"设置被测串口波特率为: {baudrate}")
        success = self.send_command(f"uart_set_baud {baudrate}")
        
        if not success:
            self.logger.error(f"设置波特率命令发送失败: {baudrate}")
            return False
            
        if success and self.test_ser:
            # 重新配置被测串口波特率
            self.disconnect_test_port()
            self.test_baudrate = baudrate
            success = self.connect_test_port()
            if success:
                self.logger.info(f"成功设置被测串口波特率为: {baudrate}")
        
        return success
    
    def generate_test_chars(self, count: int) -> bytes:
        """生成随机测试字符"""
        chars = ''.join(random.choices(string.ascii_letters + string.digits, k=count))
        return chars.encode()
    
    def run_uart_test(self, baudrate: int) -> Tuple[bool, str, bytes, bytes]:
        """执行UART测试"""
        # 设置波特率
        if not self.set_baudrate(baudrate):
            return False, "设置波特率失败", b"", b""
        
        # 启动UART测试
        if not self.send_command("uart_test"):
            return False, "启动UART测试失败", b"", b""
        
        # 生成测试数据
        test_data = self.generate_test_chars(TEST_CHAR_COUNT)
        self.logger.info(f"向测试串口发送数据: {test_data} ")
        start_time = time.time()
        
        # 发送测试数据
        try:
            # 逐字符发送测试数据
            sent_data = []
            for i, char in enumerate(test_data):
                self.test_ser.write(bytes([char]))
                sent_data.append(char)
                # Log every 10 characters to avoid excessive logging
                if i % 10 == 0:
                    self.logger.debug(f"Sent {i+1}/{len(test_data)} characters")
                time.sleep(0.01)  # 字符间短暂延迟
            
            # 发送停止字符
            self.test_ser.write(STOP_CHAR)
            
            # 逐字符接收响应数据
            response_data = []
            while True:
                char = self.test_ser.read(1)  # 读取单个字符
                if not char or char == STOP_CHAR:
                    break
                response_data.append(char[0])
                time.sleep(0.01)  # 短暂延迟
            end_time = time.time()
            duration = end_time - start_time
            # 将字节列表转换为字符串
            received_str = ''.join([chr(b) for b in response_data])
            self.logger.info(f"从测试串口接收数据: {received_str}")
            
            sent_bytes = bytes(sent_data)
            received_bytes = bytes(response_data)
            
            # 验证结果
            success = sent_bytes == received_bytes
            self.logger.info(f"测试结果: {'PASSED' if success else 'FAILED'}")
            if not success:
                self.logger.error(f"数据不匹配 - 发送: {sent_bytes!r}, 接收: {received_bytes!r}")
            if success:
                return True, "测试成功", sent_bytes, received_bytes
            else:
                return False, f"数据不匹配 - 发送: {sent_bytes!r}, 接收: {received_bytes!r}", sent_bytes, received_bytes
                
        except Exception as e:
            return False, f"测试过程出错: {str(e)}", test_data, b""
    
    def record_result(self, test_name: str, success: bool, message: str) -> None:
        """记录测试结果"""
        self.test_results["total"] += 1
        if success:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
        
        self.test_results["details"].append({
            "test": test_name,
            "status": "PASS" if success else "FAIL",
            "message": message
        })
    
    def print_summary(self) -> None:
        """打印测试汇总结果"""
        print("\n" + "="*50)
        print("测试汇总结果")
        print("="*50)
        print(f"总测试数: {self.test_results['total']}")
        print(f"通过: {self.test_results['passed']}")
        print(f"失败: {self.test_results['failed']}")
        print("\n详细结果:")
        for detail in self.test_results["details"]:
            print(f"- {detail['test']}: {detail['status']} - {detail['message']}")
        print("="*50 + "\n")


@pytest.fixture(scope="session")
def debug_uart():
    """调试串口 fixture，作用域为整个测试会话"""
    debug_uart = DebugUART(DEBUG_UART_PORT, DEBUG_BAUDRATE)
    if debug_uart.connect():
        yield debug_uart
        debug_uart.disconnect()
    else:
        pytest.fail("无法连接到调试串口，请检查配置")


@pytest.fixture(scope="module")
def uart_tester(debug_uart):
    """创建UART测试器 fixture"""
    tester = UART_Tester(TEST_UART_PORT)
    yield tester
    tester.disconnect_test_port()


@pytest.fixture(autouse=True)
def ensure_test_port_connected(uart_tester):
    """自动确保测试串口已连接"""
    if not uart_tester.connect_test_port():
        pytest.fail("无法连接到被测串口，请检查配置")


@pytest.mark.uart
def test_uart_default_baudrate(uart_tester):
    """测试默认波特率下的UART功能"""
    success, msg, sent, received = uart_tester.run_uart_test(DEFAULT_BAUDRATE)
    uart_tester.record_result(
        f"UART测试 (波特率: {DEFAULT_BAUDRATE})", 
        success, 
        f"{msg} - 发送: {sent}, 接收: {received}"
    )
    assert success, msg


@pytest.mark.uart
@pytest.mark.parametrize("baudrate", TEST_BAUDRATES)
def test_uart_different_baudrates(uart_tester, baudrate):
    """测试不同波特率下的UART功能"""
    # 跳过默认波特率，因为已经在单独的测试中覆盖
    if baudrate == DEFAULT_BAUDRATE:
        pytest.skip("默认波特率已在单独测试中覆盖")
    
    success, msg, sent, received = uart_tester.run_uart_test(baudrate)
    uart_tester.record_result(
        f"UART测试 (波特率: {baudrate})", 
        success, 
        f"{msg} - 发送: {sent}, 接收: {received}"
    )
    assert success, msg


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时执行，打印汇总结果"""
    # 获取测试器实例并打印汇总
    for item in session.items:
        if hasattr(item._request, 'fixturenames') and 'uart_tester' in item._request.fixturenames:
            tester = item._request.getfixturevalue('uart_tester')
            tester.print_summary()
            break


# 命令行执行入口
if __name__ == "__main__":
    import sys
    # 允许通过命令行参数指定测试类型
    # 例如: pytest -m uart 只运行UART测试
    #      pytest -m "not i2c" 运行除了I2C之外的所有测试
    pytest.main(sys.argv)