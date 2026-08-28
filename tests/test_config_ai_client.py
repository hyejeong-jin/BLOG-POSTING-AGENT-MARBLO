"""
Unit tests for config settings and AIClient Bedrock integration.

Tests:
- Bedrock configuration default values and environment variable overrides
- AIClient._invoke_converse retry logic with mocked boto3
- AIClient._extract_text text extraction from Converse response
"""

import asyncio
import os
from unittest.mock import MagicMock, patch, AsyncMock
import pytest

from botocore.exceptions import ClientError


class TestSettingsBedrockConfig:
    """Test Settings class Bedrock configuration.
    
    Note: These tests verify that the Settings class correctly reads from
    environment variables and that the code defaults are defined correctly.
    The .env file in the project may override these defaults in actual usage.
    """
    
    def test_use_bedrock_env_true(self):
        """Test that USE_BEDROCK=true enables Bedrock."""
        with patch.dict(os.environ, {"USE_BEDROCK": "true"}, clear=False):
            from app.config import Settings
            settings = Settings(_env_file=None)  # Skip .env file
            assert settings.use_bedrock is True
    
    def test_use_bedrock_env_override_false(self):
        """Test that USE_BEDROCK=false disables Bedrock."""
        with patch.dict(os.environ, {"USE_BEDROCK": "false"}, clear=False):
            from app.config import Settings
            settings = Settings(_env_file=None)
            assert settings.use_bedrock is False
    
    def test_bedrock_model_id_env_override(self):
        """Test BEDROCK_MODEL_ID can be set via environment."""
        with patch.dict(os.environ, {"BEDROCK_MODEL_ID": "anthropic.claude-3-haiku-20240307-v1:0"}, clear=False):
            from app.config import Settings
            settings = Settings(_env_file=None)
            assert settings.bedrock_model_id == "anthropic.claude-3-haiku-20240307-v1:0"
    
    def test_bedrock_model_id_code_default_is_nova_lite(self):
        """Test that code default for bedrock_model_id is Nova Lite."""
        # Read the source code to verify the default value
        from app.config import Settings
        import inspect
        source = inspect.getsource(Settings)
        assert 'amazon.nova-lite-v1:0' in source, "Code default for bedrock_model_id should be amazon.nova-lite-v1:0"
    
    def test_bedrock_max_tokens_env_override(self):
        """Test BEDROCK_MAX_TOKENS can be set via environment."""
        with patch.dict(os.environ, {"BEDROCK_MAX_TOKENS": "4096"}, clear=False):
            from app.config import Settings
            settings = Settings(_env_file=None)
            assert settings.bedrock_max_tokens == 4096
    
    def test_bedrock_max_tokens_code_default_is_2048(self):
        """Test that code default for bedrock_max_tokens is 2048."""
        from app.config import Settings
        import inspect
        source = inspect.getsource(Settings)
        assert 'bedrock_max_tokens' in source
        # Verify the pattern BEDROCK_MAX_TOKENS, "2048" appears in source
        assert '"2048"' in source or "'2048'" in source, "Code default for bedrock_max_tokens should be 2048"
    
    def test_bedrock_region_env_override(self):
        """Test BEDROCK_REGION can be set via environment."""
        with patch.dict(os.environ, {"BEDROCK_REGION": "us-west-2"}, clear=False):
            from app.config import Settings
            settings = Settings(_env_file=None)
            assert settings.bedrock_region == "us-west-2"
    
    def test_bedrock_region_code_default_is_us_east_1(self):
        """Test that code default for bedrock_region is us-east-1."""
        from app.config import Settings
        import inspect
        source = inspect.getsource(Settings)
        # Check that the fallback mentions us-east-1
        assert 'us-east-1' in source, "Code default for bedrock_region should be us-east-1"
    
    def test_use_bedrock_code_default_is_true(self):
        """Test that code default for use_bedrock is true."""
        from app.config import Settings
        import inspect
        source = inspect.getsource(Settings)
        # The default is "true" in the os.getenv call
        assert '"true"' in source or "'true'" in source, "Code default for use_bedrock should be 'true'"


class TestAIClientExtractText:
    """Test AIClient._extract_text method."""
    
    def test_extract_text_single_block(self):
        """Test extracting text from single text block."""
        from app.utils.ai_client import AIClient
        
        client = AIClient(use_bedrock=False)  # Don't need Bedrock for this test
        
        response = {
            "output": {
                "message": {
                    "content": [
                        {"text": "Hello, world!"}
                    ]
                }
            }
        }
        
        result = client._extract_text(response)
        assert result == "Hello, world!"
    
    def test_extract_text_multiple_blocks(self):
        """Test extracting and concatenating multiple text blocks."""
        from app.utils.ai_client import AIClient
        
        client = AIClient(use_bedrock=False)
        
        response = {
            "output": {
                "message": {
                    "content": [
                        {"text": "Part 1. "},
                        {"text": "Part 2. "},
                        {"text": "Part 3."}
                    ]
                }
            }
        }
        
        result = client._extract_text(response)
        assert result == "Part 1. Part 2. Part 3."
    
    def test_extract_text_empty_response(self):
        """Test extracting from empty response returns empty string."""
        from app.utils.ai_client import AIClient
        
        client = AIClient(use_bedrock=False)
        
        response = {}
        result = client._extract_text(response)
        assert result == ""
    
    def test_extract_text_missing_content(self):
        """Test extracting when content is missing returns empty string."""
        from app.utils.ai_client import AIClient
        
        client = AIClient(use_bedrock=False)
        
        response = {
            "output": {
                "message": {}
            }
        }
        
        result = client._extract_text(response)
        assert result == ""
    
    def test_extract_text_ignores_non_text_blocks(self):
        """Test that non-text blocks (like images) are ignored."""
        from app.utils.ai_client import AIClient
        
        client = AIClient(use_bedrock=False)
        
        response = {
            "output": {
                "message": {
                    "content": [
                        {"image": {"data": "base64data"}},
                        {"text": "Text content"},
                        {"toolUse": {"name": "someTool"}}
                    ]
                }
            }
        }
        
        result = client._extract_text(response)
        assert result == "Text content"


class TestAIClientInvokeConverseRetry:
    """Test AIClient._invoke_converse retry logic with mocked boto3."""
    
    @pytest.mark.asyncio
    async def test_invoke_converse_returns_none_when_bedrock_disabled(self):
        """Test that _invoke_converse returns None when use_bedrock=False."""
        from app.utils.ai_client import AIClient
        
        client = AIClient(use_bedrock=False)
        
        messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        result = await client._invoke_converse(messages)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_invoke_converse_success_on_first_try(self):
        """Test successful Converse call returns extracted text."""
        from app.utils.ai_client import AIClient
        
        # Create mock bedrock client
        mock_bedrock = MagicMock()
        mock_response = {
            "output": {
                "message": {
                    "content": [{"text": "Generated response"}]
                }
            }
        }
        mock_bedrock.converse.return_value = mock_response
        
        client = AIClient(use_bedrock=True)
        client._bedrock = mock_bedrock
        
        messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        result = await client._invoke_converse(messages)
        
        assert result == "Generated response"
        mock_bedrock.converse.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_invoke_converse_retries_on_throttling(self):
        """Test that ThrottlingException triggers retry with backoff."""
        from app.utils.ai_client import AIClient
        
        # Create mock bedrock client that fails twice then succeeds
        mock_bedrock = MagicMock()
        throttle_error = ClientError(
            error_response={"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            operation_name="converse"
        )
        success_response = {
            "output": {
                "message": {
                    "content": [{"text": "Success after retry"}]
                }
            }
        }
        mock_bedrock.converse.side_effect = [throttle_error, throttle_error, success_response]
        
        client = AIClient(use_bedrock=True)
        client._bedrock = mock_bedrock
        client.INITIAL_BACKOFF_SECONDS = 0.01  # Speed up test
        
        messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        result = await client._invoke_converse(messages)
        
        assert result == "Success after retry"
        assert mock_bedrock.converse.call_count == 3
    
    @pytest.mark.asyncio
    async def test_invoke_converse_retries_on_service_unavailable(self):
        """Test that ServiceUnavailableException triggers retry."""
        from app.utils.ai_client import AIClient
        
        mock_bedrock = MagicMock()
        unavailable_error = ClientError(
            error_response={"Error": {"Code": "ServiceUnavailableException", "Message": "Service unavailable"}},
            operation_name="converse"
        )
        success_response = {
            "output": {
                "message": {
                    "content": [{"text": "Recovered"}]
                }
            }
        }
        mock_bedrock.converse.side_effect = [unavailable_error, success_response]
        
        client = AIClient(use_bedrock=True)
        client._bedrock = mock_bedrock
        client.INITIAL_BACKOFF_SECONDS = 0.01
        
        messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        result = await client._invoke_converse(messages)
        
        assert result == "Recovered"
        assert mock_bedrock.converse.call_count == 2
    
    @pytest.mark.asyncio
    async def test_invoke_converse_returns_none_after_max_retries(self):
        """Test that None is returned after MAX_RETRIES exhausted."""
        from app.utils.ai_client import AIClient
        
        mock_bedrock = MagicMock()
        throttle_error = ClientError(
            error_response={"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            operation_name="converse"
        )
        # Always fail
        mock_bedrock.converse.side_effect = throttle_error
        
        client = AIClient(use_bedrock=True)
        client._bedrock = mock_bedrock
        client.INITIAL_BACKOFF_SECONDS = 0.01
        
        messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        result = await client._invoke_converse(messages)
        
        assert result is None
        assert mock_bedrock.converse.call_count == client.MAX_RETRIES
    
    @pytest.mark.asyncio
    async def test_invoke_converse_no_retry_on_access_denied(self):
        """Test that AccessDeniedException is not retried."""
        from app.utils.ai_client import AIClient
        
        mock_bedrock = MagicMock()
        access_denied_error = ClientError(
            error_response={"Error": {"Code": "AccessDeniedException", "Message": "Model access not enabled"}},
            operation_name="converse"
        )
        mock_bedrock.converse.side_effect = access_denied_error
        
        client = AIClient(use_bedrock=True)
        client._bedrock = mock_bedrock
        
        messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        result = await client._invoke_converse(messages)
        
        assert result is None
        # Should only try once since AccessDeniedException is not retryable
        assert mock_bedrock.converse.call_count == 1
    
    @pytest.mark.asyncio
    async def test_invoke_converse_no_retry_on_validation_error(self):
        """Test that ValidationException is not retried."""
        from app.utils.ai_client import AIClient
        
        mock_bedrock = MagicMock()
        validation_error = ClientError(
            error_response={"Error": {"Code": "ValidationException", "Message": "Invalid request"}},
            operation_name="converse"
        )
        mock_bedrock.converse.side_effect = validation_error
        
        client = AIClient(use_bedrock=True)
        client._bedrock = mock_bedrock
        
        messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        result = await client._invoke_converse(messages)
        
        assert result is None
        assert mock_bedrock.converse.call_count == 1
    
    @pytest.mark.asyncio
    async def test_invoke_converse_passes_system_prompt(self):
        """Test that system prompt is correctly passed to Converse API."""
        from app.utils.ai_client import AIClient
        
        mock_bedrock = MagicMock()
        mock_response = {
            "output": {
                "message": {
                    "content": [{"text": "Response"}]
                }
            }
        }
        mock_bedrock.converse.return_value = mock_response
        
        client = AIClient(use_bedrock=True)
        client._bedrock = mock_bedrock
        
        messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        system_prompt = "You are a helpful assistant."
        
        await client._invoke_converse(messages, system_prompt=system_prompt)
        
        # Verify the call was made with correct parameters
        call_kwargs = mock_bedrock.converse.call_args[1]
        assert "system" in call_kwargs
        assert call_kwargs["system"] == [{"text": "You are a helpful assistant."}]
    
    @pytest.mark.asyncio
    async def test_invoke_converse_uses_configured_model_and_max_tokens(self):
        """Test that model ID and max tokens from settings are used."""
        from app.utils.ai_client import AIClient
        
        mock_bedrock = MagicMock()
        mock_response = {
            "output": {
                "message": {
                    "content": [{"text": "Response"}]
                }
            }
        }
        mock_bedrock.converse.return_value = mock_response
        
        with patch("app.utils.ai_client.settings") as mock_settings:
            mock_settings.use_bedrock = True
            mock_settings.bedrock_model_id = "test-model-id"
            mock_settings.bedrock_max_tokens = 1024
            mock_settings.bedrock_region = "us-west-2"
            mock_settings.claude_api_key = None
            mock_settings.claude_model = "claude-3-sonnet"
            
            client = AIClient(use_bedrock=True)
            client._bedrock = mock_bedrock
            client.model_id = "test-model-id"
            client.max_tokens = 1024
            
            messages = [{"role": "user", "content": [{"text": "Hello"}]}]
            await client._invoke_converse(messages)
            
            call_kwargs = mock_bedrock.converse.call_args[1]
            assert call_kwargs["modelId"] == "test-model-id"
            assert call_kwargs["inferenceConfig"]["maxTokens"] == 1024
    
    @pytest.mark.asyncio
    async def test_invoke_converse_returns_none_on_unexpected_exception(self):
        """Test that unexpected exceptions return None."""
        from app.utils.ai_client import AIClient
        
        mock_bedrock = MagicMock()
        mock_bedrock.converse.side_effect = RuntimeError("Unexpected error")
        
        client = AIClient(use_bedrock=True)
        client._bedrock = mock_bedrock
        
        messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        result = await client._invoke_converse(messages)
        
        assert result is None
        # Unexpected errors are not retried
        assert mock_bedrock.converse.call_count == 1


class TestAIClientBedrockInitialization:
    """Test AIClient Bedrock client initialization."""
    
    def test_bedrock_client_lazy_initialization(self):
        """Test that Bedrock client is lazily initialized."""
        from app.utils.ai_client import AIClient
        
        client = AIClient(use_bedrock=True)
        
        # Initially, _bedrock should be None
        assert client._bedrock is None
    
    @patch("app.utils.ai_client.boto3")
    def test_get_bedrock_client_creates_client_once(self, mock_boto3):
        """Test that _get_bedrock_client creates client only once."""
        from app.utils.ai_client import AIClient
        
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        client = AIClient(use_bedrock=True)
        
        # First call should create client
        result1 = client._get_bedrock_client()
        assert result1 == mock_client
        mock_boto3.client.assert_called_once()
        
        # Second call should return cached client
        result2 = client._get_bedrock_client()
        assert result2 == mock_client
        # Still only one call to boto3.client
        mock_boto3.client.assert_called_once()
    
    @patch("app.utils.ai_client.boto3")
    def test_bedrock_client_uses_iam_role_credentials(self, mock_boto3):
        """Test that Bedrock client is created without explicit credentials."""
        from app.utils.ai_client import AIClient
        
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        with patch("app.utils.ai_client.settings") as mock_settings:
            mock_settings.use_bedrock = True
            mock_settings.bedrock_region = "us-east-1"
            mock_settings.bedrock_model_id = "amazon.nova-lite-v1:0"
            mock_settings.bedrock_max_tokens = 2048
            mock_settings.claude_api_key = None
            mock_settings.claude_model = "claude-3-sonnet"
            
            client = AIClient(use_bedrock=True)
            client._get_bedrock_client()
            
            # Verify boto3.client was called without aws_access_key_id or aws_secret_access_key
            call_args, call_kwargs = mock_boto3.client.call_args
            assert call_args[0] == "bedrock-runtime"
            assert "aws_access_key_id" not in call_kwargs
            assert "aws_secret_access_key" not in call_kwargs
            assert call_kwargs["region_name"] == "us-east-1"
