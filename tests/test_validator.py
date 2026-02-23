import pytest
from app.services.validator import Validator
from app.models.route import RouteValidator


class TestValidator:
    """测试验证器功能"""

    @pytest.fixture
    def validator(self):
        """创建验证器实例"""
        return Validator()

    def test_validate_required_fields(self, validator):
        """测试必填字段验证"""
        # 测试缺少必填字段
        route_validator = RouteValidator(
            required_fields=["name", "email"],
            field_types=None,
            field_ranges=None,
            validate_jwt=False,
            validate_oauth=False,
            jwt_secret=None,
            jwt_algorithm=None,
            oauth_token=None
        )
        
        # 测试空请求体
        is_valid, message = validator.validate_request(route_validator, body={})
        assert not is_valid
        assert "缺少必填字段" in message
        
        # 测试缺少部分必填字段
        is_valid, message = validator.validate_request(route_validator, body={"name": "test"})
        assert not is_valid
        assert "缺少必填字段" in message
        
        # 测试所有必填字段都存在
        is_valid, message = validator.validate_request(route_validator, body={"name": "test", "email": "test@example.com"})
        assert is_valid
        assert message is None

    def test_validate_field_types(self, validator):
        """测试字段类型验证"""
        route_validator = RouteValidator(
            required_fields=None,
            field_types={"name": "string", "age": "integer", "active": "boolean"},
            field_ranges=None,
            validate_jwt=False,
            validate_oauth=False,
            jwt_secret=None,
            jwt_algorithm=None,
            oauth_token=None
        )
        
        # 测试类型正确
        is_valid, message = validator.validate_request(
            route_validator, 
            body={"name": "test", "age": 25, "active": True}
        )
        assert is_valid
        assert message is None
        
        # 测试类型错误
        is_valid, message = validator.validate_request(
            route_validator, 
            body={"name": "test", "age": "25", "active": True}
        )
        assert not is_valid
        assert "类型错误" in message

    def test_validate_field_ranges(self, validator):
        """测试字段值范围验证"""
        route_validator = RouteValidator(
            required_fields=None,
            field_types=None,
            field_ranges={"age": [18, 65], "status": ["active", "inactive"]},
            validate_jwt=False,
            validate_oauth=False,
            jwt_secret=None,
            jwt_algorithm=None,
            oauth_token=None
        )
        
        # 测试范围正确
        is_valid, message = validator.validate_request(
            route_validator, 
            body={"age": 25, "status": "active"}
        )
        assert is_valid
        assert message is None
        
        # 测试数值范围错误
        is_valid, message = validator.validate_request(
            route_validator, 
            body={"age": 15, "status": "active"}
        )
        assert not is_valid
        assert "值超出范围" in message
        
        # 测试枚举值错误
        is_valid, message = validator.validate_request(
            route_validator, 
            body={"age": 25, "status": "unknown"}
        )
        assert not is_valid
        assert "值超出范围" in message

    def test_validate_jwt(self, validator):
        """测试JWT令牌验证"""
        route_validator = RouteValidator(
            required_fields=None,
            field_types=None,
            field_ranges=None,
            validate_jwt=True,
            validate_oauth=False,
            jwt_secret="test-secret",
            jwt_algorithm="HS256",
            oauth_token=None
        )
        
        # 测试缺少HTTP头部
        is_valid, message = validator.validate_request(route_validator, headers={})
        assert not is_valid
        assert "缺少HTTP头部" in message
        
        # 测试Authorization头部格式错误
        is_valid, message = validator.validate_request(
            route_validator, 
            headers={"Authorization": "Token test"}
        )
        assert not is_valid
        assert "格式错误" in message

    def test_validate_oauth(self, validator):
        """测试OAuth令牌验证"""
        route_validator = RouteValidator(
            required_fields=None,
            field_types=None,
            field_ranges=None,
            validate_jwt=False,
            validate_oauth=True,
            jwt_secret=None,
            jwt_algorithm=None,
            oauth_token="test-oauth-token"
        )
        
        # 测试缺少HTTP头部
        is_valid, message = validator.validate_request(route_validator, headers={})
        assert not is_valid
        assert "缺少HTTP头部" in message
        
        # 测试OAuth令牌错误
        is_valid, message = validator.validate_request(
            route_validator, 
            headers={"Authorization": "Bearer wrong-token"}
        )
        assert not is_valid
        assert "无效的OAuth令牌" in message
        
        # 测试OAuth令牌正确
        is_valid, message = validator.validate_request(
            route_validator, 
            headers={"Authorization": "Bearer test-oauth-token"}
        )
        assert is_valid
        assert message is None

    def test_validate_type(self, validator):
        """测试类型验证辅助方法"""
        assert validator._validate_type("test", "string")
        assert validator._validate_type(25, "number")
        assert validator._validate_type(25, "integer")
        assert validator._validate_type(True, "boolean")
        assert validator._validate_type([1, 2, 3], "array")
        assert validator._validate_type({"key": "value"}, "object")
        assert validator._validate_type(None, "null")
        assert not validator._validate_type(25, "string")
        assert not validator._validate_type("test", "integer")

    def test_validate_range(self, validator):
        """测试范围验证辅助方法"""
        # 测试数值范围
        assert validator._validate_range(25, [18, 65])
        assert not validator._validate_range(15, [18, 65])
        
        # 测试枚举值
        assert validator._validate_range("active", ["active", "inactive"])
        assert not validator._validate_range("unknown", ["active", "inactive"])
        
        # 测试最小值
        assert validator._validate_range(25, [18])
        assert not validator._validate_range(15, [18])
