#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TCP價格伺服器模組
為OrderTester提供TCP價格廣播功能

🏷️ TCP_PRICE_SERVER_2025_07_01
✅ 支援多客戶端連接
✅ 非阻塞IO處理
✅ 自動斷線檢測
✅ 錯誤恢復機制
"""

import socket
import threading
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class PriceServer:
    """簡化TCP價格伺服器 - 避免GIL衝突"""

    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.clients: List[socket.socket] = []
        self.running = False

        # 簡化線程管理 - 只使用一個主線程
        self.main_thread: Optional[threading.Thread] = None

        # 統計資訊
        self.total_messages_sent = 0
        self.connected_clients = 0
        self.start_time = None

        # GIL錯誤檢測
        self.gil_error_detected = False
        
    def start_server(self) -> bool:
        """啟動簡化TCP伺服器"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # 設定非阻塞模式，避免線程阻塞
            self.server_socket.setblocking(False)

            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)

            self.running = True
            self.start_time = datetime.now()

            # 啟動單一主線程，使用daemon避免GIL問題
            self.main_thread = threading.Thread(
                target=self._main_loop,
                daemon=True,
                name="TCPPriceServer"
            )
            self.main_thread.start()

            logger.info(f"✅ 簡化TCP價格伺服器已啟動 - {self.host}:{self.port}")
            return True

        except Exception as e:
            logger.error(f"❌ 啟動TCP伺服器失敗: {e}")
            return False
    
    def stop_server(self):
        """停止簡化TCP伺服器"""
        try:
            self.running = False

            # 關閉所有客戶端連接
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
            self.connected_clients = 0

            # 關閉伺服器socket
            if self.server_socket:
                try:
                    self.server_socket.close()
                except:
                    pass
                self.server_socket = None

            # 等待主線程結束 (最多2秒)
            if self.main_thread and self.main_thread.is_alive():
                self.main_thread.join(timeout=2.0)

            logger.info("⏹️ 簡化TCP價格伺服器已停止")

        except Exception as e:
            logger.error(f"❌ 停止TCP伺服器失敗: {e}")
    
    def _main_loop(self):
        """簡化主循環 - 單線程處理所有連接"""
        logger.info("🔄 TCP伺服器主循環已啟動")

        while self.running and not self.gil_error_detected:
            try:
                # 1. 接受新連接 (非阻塞)
                self._accept_new_connections()

                # 2. 清理斷開的連接
                self._cleanup_disconnected_clients()

                # 3. 短暫休眠，避免CPU過度使用
                time.sleep(0.1)

            except Exception as e:
                if "GIL" in str(e) or "PyEval_RestoreThread" in str(e):
                    logger.error(f"❌ 檢測到GIL錯誤: {e}")
                    self.gil_error_detected = True
                    self.running = False
                    break
                elif self.running:
                    logger.error(f"❌ TCP主循環錯誤: {e}")
                    time.sleep(1)  # 錯誤後等待1秒再重試

        logger.info("⏹️ TCP伺服器主循環已停止")

    def _accept_new_connections(self):
        """接受新連接 (非阻塞)"""
        try:
            while True:  # 一次處理多個連接
                try:
                    if self.server_socket:
                        client_socket, client_address = self.server_socket.accept()

                    # 設定客戶端socket為非阻塞
                    client_socket.setblocking(False)

                    self.clients.append(client_socket)
                    self.connected_clients += 1

                    logger.info(f"🔗 新客戶端連接: {client_address}")

                except BlockingIOError:
                    # 沒有新連接，正常情況
                    break
                except Exception as e:
                    logger.warning(f"⚠️ 接受連接時發生錯誤: {e}")
                    break

        except Exception as e:
            if self.running:
                logger.error(f"❌ 接受新連接失敗: {e}")

    def _cleanup_disconnected_clients(self):
        """清理斷開的客戶端"""
        try:
            active_clients = []
            disconnected_count = 0

            for client in self.clients:
                try:
                    # 發送心跳檢測 (非阻塞)
                    client.send(b'ping\n')
                    active_clients.append(client)
                except BlockingIOError:
                    # 發送緩衝區滿，但連接仍有效
                    active_clients.append(client)
                except (ConnectionResetError, BrokenPipeError):
                    # 客戶端已斷開
                    try:
                        client.close()
                    except:
                        pass
                    disconnected_count += 1
                except OSError as e:
                    # 其他網路錯誤
                    logger.warning(f"⚠️ 客戶端網路錯誤: {e}")
                    try:
                        client.close()
                    except:
                        pass
                    disconnected_count += 1
                except Exception as e:
                    logger.warning(f"⚠️ 檢查客戶端連接時發生錯誤: {e}")
                    try:
                        client.close()
                    except:
                        pass
                    disconnected_count += 1

            self.clients = active_clients
            self.connected_clients = len(active_clients)

            if disconnected_count > 0:
                logger.info(f"🧹 清理了 {disconnected_count} 個斷開的連接")

        except Exception as e:
            logger.error(f"❌ 清理客戶端連接失敗: {e}")
    

    
    def broadcast_price(self, price_data: Dict[str, Any]) -> bool:
        """簡化廣播價格資料給所有客戶端"""
        if not self.running or not self.clients or self.gil_error_detected:
            return False

        try:
            # 準備JSON訊息
            message = json.dumps(price_data) + '\n'
            message_bytes = message.encode('utf-8')

            # 廣播給所有客戶端 (簡化版本)
            active_clients = []
            successful_sends = 0

            for client in self.clients:
                try:
                    # 非阻塞發送
                    client.send(message_bytes)
                    active_clients.append(client)
                    successful_sends += 1
                except BlockingIOError:
                    # 發送緩衝區滿，跳過這次發送但保留連接
                    active_clients.append(client)
                except (ConnectionResetError, BrokenPipeError, OSError):
                    # 客戶端已斷開，不加入active_clients
                    try:
                        client.close()
                    except:
                        pass
                except Exception as e:
                    logger.warning(f"⚠️ 廣播到客戶端失敗: {e}")
                    try:
                        client.close()
                    except:
                        pass

            # 更新客戶端列表
            self.clients = active_clients
            self.connected_clients = len(active_clients)

            if successful_sends > 0:
                self.total_messages_sent += 1
                return True

            return False

        except Exception as e:
            if "GIL" in str(e) or "PyEval_RestoreThread" in str(e):
                logger.error(f"❌ 廣播時檢測到GIL錯誤: {e}")
                self.gil_error_detected = True
                self.running = False
            else:
                logger.error(f"❌ 廣播價格失敗: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """獲取伺服器狀態"""
        uptime = None
        if self.start_time:
            uptime = datetime.now() - self.start_time
            
        return {
            'running': self.running,
            'host': self.host,
            'port': self.port,
            'connected_clients': len(self.clients),
            'total_messages_sent': self.total_messages_sent,
            'uptime': str(uptime) if uptime else None
        }

class PriceClient:
    """簡化TCP價格客戶端 - 避免GIL衝突"""

    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.running = False

        # 簡化線程管理 - 只使用一個接收線程
        self.receive_thread: Optional[threading.Thread] = None
        self.price_callback = None

        # 統計資訊
        self.total_messages_received = 0
        self.last_price_time = None

        # GIL錯誤檢測
        self.gil_error_detected = False

        # 接收緩衝區
        self.receive_buffer = ""
        
    def connect(self) -> bool:
        """連接到價格伺服器 (增強日誌版本)"""
        try:
            logger.info(f"🔗 PriceClient開始連接到 {self.host}:{self.port}")

            # 檢查是否已連接
            if self.connected:
                logger.warning("PriceClient已連接，跳過重複連接")
                return True

            # 清理舊連接
            if self.socket:
                logger.info("清理舊socket連接")
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None

            # 建立新socket
            logger.info("建立新socket連接")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)  # 5秒連接超時

            # 嘗試連接
            logger.info(f"嘗試連接到 {self.host}:{self.port} (超時: 5秒)")
            connect_start = time.time()
            self.socket.connect((self.host, self.port))
            connect_time = time.time() - connect_start

            logger.info(f"Socket連接成功，耗時: {connect_time:.3f}秒")

            # 連接成功後設為非阻塞模式
            self.socket.setblocking(False)
            logger.info("Socket已設為非阻塞模式")

            self.connected = True
            self.running = True
            self.gil_error_detected = False
            self.receive_buffer = ""  # 清空接收緩衝區

            # 啟動簡化接收線程
            logger.info("啟動TCP接收線程")
            self.receive_thread = threading.Thread(
                target=self._receive_messages_simple,
                daemon=True,
                name="TCPPriceClient"
            )
            self.receive_thread.start()

            logger.info(f"✅ PriceClient已連接到價格伺服器 - {self.host}:{self.port}")
            return True

        except ConnectionRefusedError:
            logger.error(f"❌ 連接被拒絕 - TCP伺服器可能未啟動 ({self.host}:{self.port})")
            return False
        except socket.timeout:
            logger.error(f"❌ 連接超時 - TCP伺服器無響應 ({self.host}:{self.port})")
            return False
        except OSError as e:
            if e.errno == 10061:  # Windows: No connection could be made
                logger.error(f"❌ 無法連接到伺服器 - 請確認OrderTester已啟動TCP伺服器 (錯誤: {e})")
            else:
                logger.error(f"❌ 網路錯誤 (errno: {e.errno}): {e}")
            return False
        except Exception as e:
            logger.error(f"❌ PriceClient連接失敗: {e}", exc_info=True)
            return False
    
    def disconnect(self):
        """斷開連接 (簡化版本)"""
        try:
            self.running = False
            self.connected = False

            # 關閉socket
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None

            # 等待接收線程結束 (最多2秒)
            if self.receive_thread and self.receive_thread.is_alive():
                self.receive_thread.join(timeout=2.0)

            # 清理緩衝區
            self.receive_buffer = ""

            logger.info("🔌 已斷開價格伺服器連接")

        except Exception as e:
            logger.error(f"❌ 斷開連接失敗: {e}")
    
    def _receive_messages_simple(self):
        """簡化接收訊息線程 - 避免GIL衝突"""
        logger.info("🔄 TCP客戶端接收線程已啟動")

        while self.running and self.connected and not self.gil_error_detected:
            try:
                # 非阻塞接收數據
                self._receive_data_non_blocking()

                # 處理完整訊息
                self._process_complete_messages()

                # 短暫休眠，避免CPU過度使用
                time.sleep(0.05)

            except Exception as e:
                if "GIL" in str(e) or "PyEval_RestoreThread" in str(e):
                    logger.error(f"❌ 客戶端檢測到GIL錯誤: {e}")
                    self.gil_error_detected = True
                    self.connected = False
                    break
                elif self.running:
                    logger.error(f"❌ 接收訊息失敗: {e}")
                    time.sleep(1)  # 錯誤後等待1秒再重試

        # 連接斷開
        self.connected = False
        logger.info("⏹️ TCP客戶端接收線程已停止")

    def _receive_data_non_blocking(self):
        """非阻塞接收數據"""
        try:
            if self.socket:
                data = self.socket.recv(1024).decode('utf-8')
                if data:
                    self.receive_buffer += data
                else:
                    # 伺服器關閉連接
                    self.connected = False
        except BlockingIOError:
            # 沒有數據可讀，正常情況
            pass
        except (ConnectionResetError, BrokenPipeError):
            # 連接已斷開
            self.connected = False
        except Exception as e:
            logger.warning(f"⚠️ 接收數據時發生錯誤: {e}")
            self.connected = False

    def _process_complete_messages(self):
        """處理完整的訊息"""
        try:
            # 處理完整的訊息（以換行符分隔）
            while '\n' in self.receive_buffer:
                line, self.receive_buffer = self.receive_buffer.split('\n', 1)

                if line.strip() == 'ping':
                    continue  # 忽略心跳

                if line.strip():  # 非空行
                    try:
                        price_data = json.loads(line)
                        self._handle_price_data(price_data)
                    except json.JSONDecodeError:
                        logger.warning(f"⚠️ JSON解析失敗: {line}")
                        continue

        except Exception as e:
            logger.error(f"❌ 處理訊息失敗: {e}")
    
    def _handle_price_data(self, price_data: Dict[str, Any]):
        """處理接收到的價格資料"""
        try:
            self.total_messages_received += 1
            self.last_price_time = datetime.now()
            
            # 回調策略處理函數
            if self.price_callback:
                self.price_callback(price_data)
                
        except Exception as e:
            logger.error(f"❌ 處理價格資料失敗: {e}")
    
    def set_price_callback(self, callback):
        """設定價格回調函數"""
        self.price_callback = callback
    
    def get_status(self) -> Dict[str, Any]:
        """獲取客戶端狀態"""
        return {
            'connected': self.connected,
            'host': self.host,
            'port': self.port,
            'total_messages_received': self.total_messages_received,
            'last_price_time': self.last_price_time.strftime('%H:%M:%S.%f')[:-3] if self.last_price_time else None
        }

# 全域伺服器實例
_price_server: Optional[PriceServer] = None

def start_price_server(host='localhost', port=8888) -> bool:
    """啟動全域價格伺服器"""
    global _price_server
    
    if _price_server and _price_server.running:
        logger.warning("價格伺服器已在運行中")
        return True
    
    _price_server = PriceServer(host, port)
    return _price_server.start_server()

def stop_price_server():
    """停止全域價格伺服器"""
    global _price_server
    
    if _price_server:
        _price_server.stop_server()
        _price_server = None

def broadcast_price_tcp(price_data: Dict[str, Any]) -> bool:
    """廣播價格資料（全域函數）"""
    global _price_server
    
    if _price_server and _price_server.running:
        return _price_server.broadcast_price(price_data)
    return False

def get_server_status() -> Optional[Dict[str, Any]]:
    """獲取伺服器狀態"""
    global _price_server
    
    if _price_server:
        return _price_server.get_status()
    return None
