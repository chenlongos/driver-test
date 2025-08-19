import pytest
import serial
import random
import string
import time
import logging
from typing import List, Dict, Tuple

# 测试配置
TEST_UART_PORT = "/dev/ttyUSB1"   # 被测串口，波特率可设置
DEFAULT_BAUDRATE = 115200          # 被测串口默认波特率
TEST_BAUDRATES = [9600, 19200, 38400, 57600, 230400]
TEST_CHAR_COUNT = 10
STOP_CHAR = b'\x00'  # 停止发送的字符

class UART_Tester:
    def __init__(self, debug_uart):
        self.logger = logging.getLogger('UART_Tester')
        self.test_result = False 
        self.debug_uart = debug_uart
        self.test_ser = None
        self.test_port = TEST_UART_PORT
        self.test_baudrate = DEFAULT_BAUDRATE

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
                return True, "测试成功"
            else:
                return False, f"数据不匹配 - 发送: {sent_bytes!r}, 接收: {received_bytes!r}"
                
        except Exception as e:
            return False, f"测试过程出错: {str(e)}", test_data, b""
    
@pytest.fixture(scope="module")
def uart_tester(debug_uart):
    """创建UART测试器 fixture"""
    tester = UART_Tester(debug_uart)
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
    success, msg = uart_tester.run_uart_test(DEFAULT_BAUDRATE)
    assert success, msg


@pytest.mark.uart
@pytest.mark.parametrize("baudrate", TEST_BAUDRATES)
def test_uart_different_baudrates(uart_tester, baudrate):
    """测试不同波特率下的UART功能"""
    # 跳过默认波特率，因为已经在单独的测试中覆盖
    if baudrate == DEFAULT_BAUDRATE:
        pytest.skip("默认波特率已在单独测试中覆盖")
    
    success, msg = uart_tester.run_uart_test(baudrate)
    assert success, msg

