import sqlite3
import json
import os
from typing import List, Optional, Dict, Any
from app.models.request import Request as RequestModel
from app.models.response import Response as ResponseModel
from app.core.config import config


class DatabaseStorage:
    """数据库存储系统"""
    
    def __init__(self, db_path: Optional[str] = None):
        """初始化数据库存储
        
        Args:
            db_path: 数据库文件路径，默认使用配置中的路径
        """
        self.db_path = db_path or config.storage.db_path
        # 确保数据库文件目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()
    
    def init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建请求表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS requests (
                    id TEXT PRIMARY KEY,
                    timestamp REAL,
                    method TEXT,
                    path TEXT,
                    query_params TEXT,
                    headers TEXT,
                    body TEXT,
                    client_ip TEXT,
                    matched_route_id TEXT,
                    response_status INTEGER,
                    response_time REAL
                )
            ''')
            
            # 创建响应表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS responses (
                    id TEXT PRIMARY KEY,
                    request_id TEXT,
                    timestamp REAL,
                    status_code INTEGER,
                    headers TEXT,
                    content TEXT,
                    content_type TEXT,
                    response_time REAL,
                    delay_applied REAL,
                    FOREIGN KEY (request_id) REFERENCES requests (id)
                )
            ''')
            
            # 创建配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    value TEXT,
                    created_at REAL,
                    updated_at REAL
                )
            ''')
            
            conn.commit()
    
    def save_request(self, request: RequestModel):
        """保存请求记录
        
        Args:
            request: 请求模型实例
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT OR REPLACE INTO requests 
                (id, timestamp, method, path, query_params, headers, body, client_ip, matched_route_id, response_status, response_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    request.id,
                    request.timestamp,
                    request.method,
                    request.path,
                    json.dumps(request.query_params),
                    json.dumps(request.headers),
                    json.dumps(request.body),
                    request.client_ip,
                    request.matched_route_id,
                    request.response_status,
                    request.response_time
                )
            )
            conn.commit()
    
    def save_response(self, response: ResponseModel):
        """保存响应记录
        
        Args:
            response: 响应模型实例
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT OR REPLACE INTO responses 
                (id, request_id, timestamp, status_code, headers, content, content_type, response_time, delay_applied)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    response.id,
                    response.request_id,
                    response.timestamp,
                    response.status_code,
                    json.dumps(response.headers),
                    json.dumps(response.content),
                    response.content_type,
                    response.response_time,
                    response.delay_applied
                )
            )
            conn.commit()
    
    def get_requests(self, limit: int = 1000, offset: int = 0, start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[RequestModel]:
        """获取请求记录
        
        Args:
            limit: 返回记录数量限制
            offset: 偏移量
            start_time: 开始时间戳
            end_time: 结束时间戳
            
        Returns:
            请求记录列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 构建查询语句
            query = 'SELECT * FROM requests '
            params = []
            
            # 添加时间范围过滤
            if start_time is not None or end_time is not None:
                query += 'WHERE '
                if start_time is not None:
                    query += 'timestamp >= ? '
                    params.append(start_time)
                if start_time is not None and end_time is not None:
                    query += 'AND '
                if end_time is not None:
                    query += 'timestamp <= ? '
                    params.append(end_time)
            
            # 添加排序和分页
            query += 'ORDER BY timestamp DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            requests = []
            for row in rows:
                # 处理 timestamp 字段，确保转换为浮点数
                timestamp = row['timestamp']
                if isinstance(timestamp, str):
                    try:
                        # 尝试从字符串转换为时间戳
                        import datetime
                        from dateutil import parser
                        dt = parser.parse(timestamp)
                        timestamp = dt.timestamp()
                    except:
                        # 如果转换失败，使用当前时间
                        import time
                        timestamp = time.time()
                elif not isinstance(timestamp, float):
                    # 确保是浮点数
                    timestamp = float(timestamp)
                
                request = RequestModel(
                    id=row['id'],
                    timestamp=timestamp,
                    method=row['method'],
                    path=row['path'],
                    query_params=json.loads(row['query_params']),
                    headers=json.loads(row['headers']),
                    body=json.loads(row['body']),
                    client_ip=row['client_ip'],
                    matched_route_id=row['matched_route_id'],
                    response_status=row['response_status'],
                    response_time=row['response_time']
                )
                requests.append(request)
            
            return requests
    
    def get_request_by_id(self, request_id: str) -> Optional[RequestModel]:
        """根据ID获取请求记录
        
        Args:
            request_id: 请求ID
            
        Returns:
            请求记录或None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT * FROM requests 
                WHERE id = ?
                ''',
                (request_id,)
            )
            row = cursor.fetchone()
            
            if row:
                # 处理 timestamp 字段，确保转换为浮点数
                timestamp = row['timestamp']
                if isinstance(timestamp, str):
                    try:
                        # 尝试从字符串转换为时间戳
                        import datetime
                        from dateutil import parser
                        dt = parser.parse(timestamp)
                        timestamp = dt.timestamp()
                    except:
                        # 如果转换失败，使用当前时间
                        import time
                        timestamp = time.time()
                elif not isinstance(timestamp, float):
                    # 确保是浮点数
                    timestamp = float(timestamp)
                
                return RequestModel(
                    id=row['id'],
                    timestamp=timestamp,
                    method=row['method'],
                    path=row['path'],
                    query_params=json.loads(row['query_params']),
                    headers=json.loads(row['headers']),
                    body=json.loads(row['body']),
                    client_ip=row['client_ip'],
                    matched_route_id=row['matched_route_id'],
                    response_status=row['response_status'],
                    response_time=row['response_time']
                )
            return None
    
    def get_response_by_request_id(self, request_id: str) -> Optional[ResponseModel]:
        """根据请求ID获取响应记录
        
        Args:
            request_id: 请求ID
            
        Returns:
            响应记录或None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT * FROM responses 
                WHERE request_id = ?
                ''',
                (request_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return ResponseModel(
                    id=row['id'],
                    request_id=row['request_id'],
                    timestamp=row['timestamp'],
                    status_code=row['status_code'],
                    headers=json.loads(row['headers']),
                    content=json.loads(row['content']),
                    content_type=row['content_type'],
                    response_time=row['response_time'],
                    delay_applied=row['delay_applied']
                )
            return None
    
    def get_request_count(self) -> int:
        """获取请求总数
        
        Returns:
            请求总数
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM requests')
            count = cursor.fetchone()[0]
            return count
    
    def clear_requests(self):
        """清空请求和响应记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM responses')
            cursor.execute('DELETE FROM requests')
            conn.commit()
    
    def save_config(self, name: str, value: Dict[str, Any]):
        """保存配置
        
        Args:
            name: 配置名称
            value: 配置值
        """
        import time
        current_time = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT OR REPLACE INTO configs 
                (name, value, created_at, updated_at)
                VALUES (?, ?, COALESCE((SELECT created_at FROM configs WHERE name = ?), ?), ?)
                ''',
                (name, json.dumps(value), name, current_time, current_time)
            )
            conn.commit()
    
    def get_config(self, name: str) -> Optional[Dict[str, Any]]:
        """获取配置
        
        Args:
            name: 配置名称
            
        Returns:
            配置值或None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT value FROM configs 
                WHERE name = ?
                ''',
                (name,)
            )
            row = cursor.fetchone()
            
            if row:
                return json.loads(row['value'])
            return None


# 创建全局数据库存储实例
db_storage = DatabaseStorage()
