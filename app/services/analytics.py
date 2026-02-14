import time
import statistics
from typing import Dict, Any, List, Optional
from collections import defaultdict
from app.storage.database import db_storage


class AnalyticsManager:
    """统计分析类"""
    
    def __init__(self):
        """初始化统计分析管理器"""
        pass
    
    def get_request_trend(self, hours: int = 24, interval: str = 'hour') -> Dict[str, Any]:
        """获取请求趋势
        
        Args:
            hours: 统计小时数
            interval: 时间间隔，可选值：'hour', 'minute'
            
        Returns:
            请求趋势数据
        """
        # 计算开始时间和结束时间
        end_time = time.time()
        start_time = end_time - (hours * 3600)
        
        # 获取请求记录
        requests = db_storage.get_requests(limit=10000)
        
        # 过滤时间范围内的请求
        filtered_requests = [req for req in requests if req.timestamp >= start_time and req.timestamp <= end_time]
        
        # 按分钟分组所有请求，确保每个请求都有自己的时间点
        minute_grouped_requests = defaultdict(list)
        for req in filtered_requests:
            # 按分钟分组
            time_key = time.strftime('%Y-%m-%d %H:%M', time.localtime(req.timestamp))
            minute_grouped_requests[time_key].append(req)
        
        # 生成时间标签和数据
        labels = []
        data = []
        response_times = []
        status_codes = defaultdict(list)
        methods = defaultdict(list)
        time_points = []  # 保存实际时间点，用于鼠标浮动显示
        
        if interval == 'hour':
            # 按小时生成标签，但按分钟统计数据
            current_time = start_time
            while current_time <= end_time:
                # 生成小时标签
                hour_label = time.strftime('%Y-%m-%d %H:00', time.localtime(current_time))
                labels.append(hour_label)
                
                # 统计该小时内的所有分钟数据
                hour_requests = []
                hour_start = current_time
                hour_end = current_time + 3600
                
                # 遍历该小时内的所有分钟
                for minute_time in range(int(hour_start), int(hour_end), 60):
                    minute_key = time.strftime('%Y-%m-%d %H:%M', time.localtime(minute_time))
                    if minute_key in minute_grouped_requests:
                        hour_requests.extend(minute_grouped_requests[minute_key])
                
                # 计算该小时的数据
                data.append(len(hour_requests))
                avg_response_time = statistics.mean([req.response_time for req in hour_requests]) if hour_requests else 0
                response_times.append(avg_response_time)
                
                # 统计状态码
                code_counts = defaultdict(int)
                for req in hour_requests:
                    code_counts[req.response_status] += 1
                status_codes[hour_label] = dict(code_counts)
                
                # 统计请求方法
                method_counts = defaultdict(int)
                for req in hour_requests:
                    method_counts[req.method] += 1
                methods[hour_label] = dict(method_counts)
                
                # 保存该小时的实际时间点（取中间时间）
                time_points.append(hour_label)
                
                # 增加1小时
                current_time += 3600
        else:
            # 按分钟生成标签和统计数据
            current_time = start_time
            while current_time <= end_time:
                # 生成分钟标签
                minute_label = time.strftime('%Y-%m-%d %H:%M', time.localtime(current_time))
                labels.append(minute_label)
                
                # 统计该分钟的数据
                minute_requests = minute_grouped_requests.get(minute_label, [])
                data.append(len(minute_requests))
                avg_response_time = statistics.mean([req.response_time for req in minute_requests]) if minute_requests else 0
                response_times.append(avg_response_time)
                
                # 统计状态码
                code_counts = defaultdict(int)
                for req in minute_requests:
                    code_counts[req.response_status] += 1
                status_codes[minute_label] = dict(code_counts)
                
                # 统计请求方法
                method_counts = defaultdict(int)
                for req in minute_requests:
                    method_counts[req.method] += 1
                methods[minute_label] = dict(method_counts)
                
                # 保存该分钟的实际时间点
                time_points.append(minute_label)
                
                # 增加1分钟
                current_time += 60
        
        return {
            'labels': labels,
            'request_counts': data,
            'response_times': response_times,
            'status_codes': dict(status_codes),
            'methods': dict(methods),
            'time_points': time_points,  # 保存实际时间点，用于前端显示
            'total_requests': len(filtered_requests),
            'time_range': {
                'start': start_time,
                'end': time.time(),
                'hours': hours
            }
        }
    
    def get_response_time_stats(self, hours: int = 24) -> Dict[str, Any]:
        """获取响应时间统计
        
        Args:
            hours: 统计小时数
            
        Returns:
            响应时间统计数据
        """
        # 计算开始时间
        start_time = time.time() - (hours * 3600)
        
        # 获取请求记录
        requests = db_storage.get_requests(limit=10000)
        
        # 过滤时间范围内的请求
        filtered_requests = [req for req in requests if req.timestamp >= start_time]
        
        if not filtered_requests:
            return {
                'total_requests': 0,
                'avg_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0,
                'p50_response_time': 0,
                'p95_response_time': 0,
                'p99_response_time': 0,
                'time_range': {
                    'start': start_time,
                    'end': time.time(),
                    'hours': hours
                }
            }
        
        # 提取响应时间
        response_times = [req.response_time for req in filtered_requests]
        
        # 计算统计数据
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        
        # 计算百分位数
        response_times.sort()
        n = len(response_times)
        p50 = response_times[int(n * 0.5)] if n > 0 else 0
        p95 = response_times[int(n * 0.95)] if n > 0 else 0
        p99 = response_times[int(n * 0.99)] if n > 0 else 0
        
        return {
            'total_requests': len(filtered_requests),
            'avg_response_time': avg_response_time,
            'min_response_time': min_response_time,
            'max_response_time': max_response_time,
            'p50_response_time': p50,
            'p95_response_time': p95,
            'p99_response_time': p99,
            'time_range': {
                'start': start_time,
                'end': time.time(),
                'hours': hours
            }
        }
    
    def get_status_code_stats(self, hours: int = 24) -> Dict[str, Any]:
        """获取状态码统计
        
        Args:
            hours: 统计小时数
            
        Returns:
            状态码统计数据
        """
        # 计算开始时间
        start_time = time.time() - (hours * 3600)
        
        # 获取请求记录
        requests = db_storage.get_requests(limit=10000)
        
        # 过滤时间范围内的请求
        filtered_requests = [req for req in requests if req.timestamp >= start_time]
        
        # 统计状态码
        status_counts = defaultdict(int)
        for req in filtered_requests:
            status_counts[req.response_status] += 1
        
        # 按状态码分类
        status_categories = {
            '1xx': 0,
            '2xx': 0,
            '3xx': 0,
            '4xx': 0,
            '5xx': 0
        }
        
        for status_code, count in status_counts.items():
            if 100 <= status_code < 200:
                status_categories['1xx'] += count
            elif 200 <= status_code < 300:
                status_categories['2xx'] += count
            elif 300 <= status_code < 400:
                status_categories['3xx'] += count
            elif 400 <= status_code < 500:
                status_categories['4xx'] += count
            elif 500 <= status_code < 600:
                status_categories['5xx'] += count
        
        return {
            'total_requests': len(filtered_requests),
            'status_counts': dict(status_counts),
            'status_categories': status_categories,
            'time_range': {
                'start': start_time,
                'end': time.time(),
                'hours': hours
            }
        }
    
    def get_method_stats(self, hours: int = 24) -> Dict[str, Any]:
        """获取请求方法统计
        
        Args:
            hours: 统计小时数
            
        Returns:
            请求方法统计数据
        """
        # 计算开始时间
        start_time = time.time() - (hours * 3600)
        
        # 获取请求记录
        requests = db_storage.get_requests(limit=10000)
        
        # 过滤时间范围内的请求
        filtered_requests = [req for req in requests if req.timestamp >= start_time]
        
        # 统计请求方法
        method_counts = defaultdict(int)
        for req in filtered_requests:
            method_counts[req.method] += 1
        
        return {
            'total_requests': len(filtered_requests),
            'method_counts': dict(method_counts),
            'time_range': {
                'start': start_time,
                'end': time.time(),
                'hours': hours
            }
        }
    
    def get_path_stats(self, hours: int = 24, limit: int = 10) -> Dict[str, Any]:
        """获取路径统计
        
        Args:
            hours: 统计小时数
            limit: 返回路径数量限制
            
        Returns:
            路径统计数据
        """
        # 计算开始时间
        start_time = time.time() - (hours * 3600)
        
        # 获取请求记录
        requests = db_storage.get_requests(limit=10000)
        
        # 过滤时间范围内的请求
        filtered_requests = [req for req in requests if req.timestamp >= start_time]
        
        # 统计路径
        path_counts = defaultdict(int)
        path_response_times = defaultdict(list)
        
        for req in filtered_requests:
            path_counts[req.path] += 1
            path_response_times[req.path].append(req.response_time)
        
        # 计算每个路径的平均响应时间
        path_stats = []
        for path, count in path_counts.items():
            avg_response_time = statistics.mean(path_response_times[path]) if path_response_times[path] else 0
            path_stats.append({
                'path': path,
                'count': count,
                'avg_response_time': avg_response_time
            })
        
        # 按请求数排序
        path_stats.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            'total_requests': len(filtered_requests),
            'top_paths': path_stats[:limit],
            'time_range': {
                'start': start_time,
                'end': time.time(),
                'hours': hours
            }
        }
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """获取汇总统计
        
        Returns:
            汇总统计数据
        """
        # 获取所有请求记录
        requests = db_storage.get_requests(limit=10000)
        
        if not requests:
            return {
                'total_requests': 0,
                'total_response_time': 0,
                'avg_response_time': 0,
                'earliest_request': None,
                'latest_request': None,
                'status_codes': {},
                'methods': {}
            }
        
        # 计算汇总统计
        total_requests = len(requests)
        total_response_time = sum([req.response_time for req in requests])
        avg_response_time = total_response_time / total_requests if total_requests > 0 else 0
        earliest_request = min([req.timestamp for req in requests])
        latest_request = max([req.timestamp for req in requests])
        
        # 统计状态码
        status_counts = defaultdict(int)
        for req in requests:
            status_counts[req.response_status] += 1
        
        # 统计请求方法
        method_counts = defaultdict(int)
        for req in requests:
            method_counts[req.method] += 1
        
        return {
            'total_requests': total_requests,
            'total_response_time': total_response_time,
            'avg_response_time': avg_response_time,
            'earliest_request': earliest_request,
            'latest_request': latest_request,
            'status_codes': dict(status_counts),
            'methods': dict(method_counts)
        }


# 创建全局统计分析管理器实例
analytics_manager = AnalyticsManager()
