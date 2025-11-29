# Gemini 3 Pro Integration Guide

## Overview

DevOps Brain now includes full support for Google's Gemini 3 Pro (via `gemini-2.0-flash-exp`) with advanced features and best practices.

## Features Enabled

### 1. **Safety Settings**
- Automatic safety filtering for harmful content
- Configurable thresholds for harassment, hate speech, explicit content, and dangerous content
- Default: Block medium and above severity

### 2. **Function Calling**
- Full support for tool/function calling
- Automatic conversion from OpenAI format to Gemini format
- Seamless integration with existing agent tools

### 3. **Streaming Support**
- Real-time streaming responses
- Compatible with WebSocket updates
- Efficient token-by-token delivery

### 4. **Token Counting**
- Accurate token counting using Gemini's native tokenizer
- Automatic fallback to estimation if unavailable

### 5. **Multimodal Support** (Ready for future enhancement)
- Architecture supports image, video, and audio inputs
- Can be extended for design agent image processing

### 6. **Grounding** (Optional)
- Fact-checking with Google Search
- Can be enabled via configuration
- Useful for documentation and research tasks

## Configuration

### Environment Variables

```bash
# Required
export GOOGLE_API_KEY="your-api-key-here"
# OR
export GEMINI_API_KEY="your-api-key-here"
```

### Agent Configuration

The default configuration uses Gemini as the primary provider:

```yaml
llm_providers:
  primary:
    provider: "gemini"
    model: "gemini-2.0-flash-exp"
    temperature: 0.7
    max_tokens: 8192
    extra:
      grounding: false  # Enable for fact-checking
```

### Using Gemini in Code

```python
from src.core.llm import LLMConfig, LLMManager, Message, Role

# Create Gemini config
config = LLMConfig(
    provider="gemini",
    model="gemini-2.0-flash-exp",
    temperature=0.7,
    max_tokens=8192,
    extra={
        "grounding": False,  # Enable Google Search grounding
    }
)

# Initialize manager
manager = LLMManager(primary_config=config)
await manager.initialize()

# Use it
messages = [
    Message(role=Role.SYSTEM, content="You are a helpful DevOps assistant."),
    Message(role=Role.USER, content="Explain Kubernetes deployments."),
]

response = await manager.complete(messages)
print(response.content)
```

## Best Practices

### 1. **Model Selection**
- **gemini-2.0-flash-exp**: Best for general tasks, fast responses
- **gemini-1.5-pro**: Better for complex reasoning (if available)
- **gemini-1.5-flash**: Fastest, good for simple tasks

### 2. **Temperature Settings**
- **0.0-0.3**: Deterministic, code generation
- **0.4-0.7**: Balanced (default)
- **0.8-1.0**: Creative, documentation

### 3. **Token Limits**
- Default: 8192 tokens (Gemini 2.0 supports up to 1M tokens)
- Adjust based on task complexity
- Use streaming for long responses

### 4. **Safety Settings**
- Default settings block medium+ severity
- Adjust per agent if needed
- Security agent may need stricter settings

### 5. **Function Calling**
- Gemini supports function calling natively
- Tools are automatically converted
- Use for agent tool integration

## Integration with Agents

All agents can use Gemini by default. The system automatically:
1. Falls back to OpenAI if Gemini fails
2. Falls back to Anthropic if both fail
3. Caches responses for efficiency
4. Tracks usage and performance

## Performance

Gemini 3 Pro offers:
- **Fast response times**: Lower latency than GPT-4
- **Better cost efficiency**: Competitive pricing
- **Large context**: Up to 1M tokens (2.0 models)
- **Multimodal**: Ready for image/video processing

## Troubleshooting

### API Key Issues
```python
# Check environment variable
import os
print(os.environ.get("GOOGLE_API_KEY"))
```

### Import Errors
```bash
pip install google-generativeai>=0.3.0
```

### Rate Limiting
- Gemini has generous rate limits
- Manager automatically handles retries
- Check usage in manager stats

### Safety Blocks
- Adjust safety settings if too restrictive
- Check `raw_response` for block reasons
- Use different model if needed

## Advanced Features

### Grounding with Google Search
```python
config = LLMConfig(
    provider="gemini",
    model="gemini-2.0-flash-exp",
    extra={
        "grounding": True,  # Enable fact-checking
        "chunk_size": 1024,
        "chunk_overlap": 200,
    }
)
```

### Custom Safety Settings
```python
from google.generativeai.types import HarmCategory, HarmBlockThreshold

safety_settings = [
    {
        "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
        "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH,
    },
    # ... customize others
]
```

## Migration from OpenAI/Anthropic

The integration is seamless:
1. Change `provider` in config from `"openai"` to `"gemini"`
2. Update model name to `"gemini-2.0-flash-exp"`
3. No code changes needed - same interface
4. Automatic fallback ensures reliability

## Support

For issues or questions:
1. Check Gemini API documentation
2. Review error logs in `src/core/llm/providers.py`
3. Verify API key and quotas
4. Test with simple completion first
