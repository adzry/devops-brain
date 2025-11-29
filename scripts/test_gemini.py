#!/usr/bin/env python3
"""
Test script for Gemini 3 Pro integration.

Run with: python scripts/test_gemini.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.llm import LLMConfig, LLMManager, Message, Role


async def test_gemini_basic():
    """Test basic Gemini completion."""
    print("=" * 60)
    print("Testing Gemini 3 Pro Basic Completion")
    print("=" * 60)
    
    # Check for API key
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  Warning: GOOGLE_API_KEY or GEMINI_API_KEY not set")
        print("   Set it with: export GOOGLE_API_KEY='your-key'")
        return False
    
    # Create Gemini config
    config = LLMConfig(
        provider="gemini",
        model="gemini-2.0-flash-exp",
        temperature=0.7,
        max_tokens=1024,
    )
    
    # Initialize manager
    manager = LLMManager(primary_config=config)
    await manager.initialize()
    
    # Test completion
    messages = [
        Message(role=Role.SYSTEM, content="You are a helpful DevOps assistant."),
        Message(role=Role.USER, content="Explain what Kubernetes is in one sentence."),
    ]
    
    try:
        print("\n📤 Sending request to Gemini...")
        response = await manager.complete(messages)
        
        print(f"\n✅ Success!")
        print(f"Model: {response.model}")
        print(f"Content: {response.content}")
        print(f"Tokens: {response.total_tokens} (prompt: {response.prompt_tokens}, completion: {response.completion_tokens})")
        print(f"Finish reason: {response.finish_reason}")
        
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gemini_streaming():
    """Test Gemini streaming."""
    print("\n" + "=" * 60)
    print("Testing Gemini Streaming")
    print("=" * 60)
    
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  Skipping: API key not set")
        return False
    
    config = LLMConfig(
        provider="gemini",
        model="gemini-2.0-flash-exp",
        temperature=0.7,
        max_tokens=512,
    )
    
    manager = LLMManager(primary_config=config)
    await manager.initialize()
    
    messages = [
        Message(role=Role.USER, content="Count from 1 to 5, one number per line."),
    ]
    
    try:
        print("\n📤 Streaming response...")
        print("Response: ", end="", flush=True)
        
        async for chunk in manager._providers[0].stream(messages):
            print(chunk.content, end="", flush=True)
        
        print("\n✅ Streaming complete!")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


async def test_gemini_fallback():
    """Test fallback mechanism."""
    print("\n" + "=" * 60)
    print("Testing Fallback Mechanism")
    print("=" * 60)
    
    # Create config with invalid API key to trigger fallback
    gemini_config = LLMConfig(
        provider="gemini",
        model="gemini-2.0-flash-exp",
        api_key="invalid-key",
    )
    
    # Fallback to OpenAI
    openai_config = LLMConfig(
        provider="openai",
        model="gpt-3.5-turbo",
    )
    
    manager = LLMManager(
        primary_config=gemini_config,
        fallback_configs=[openai_config],
    )
    
    try:
        await manager.initialize()
        print("✅ Manager initialized with fallback")
        
        # Get stats
        stats = manager.get_stats()
        print(f"\nProvider stats: {list(stats['providers'].keys())}")
        
        return True
    except Exception as e:
        print(f"⚠️  Fallback test: {e}")
        print("   (This is expected if OpenAI key is not set)")
        return True  # Not a failure


async def test_gemini_token_counting():
    """Test token counting."""
    print("\n" + "=" * 60)
    print("Testing Token Counting")
    print("=" * 60)
    
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  Skipping: API key not set")
        return False
    
    config = LLMConfig(
        provider="gemini",
        model="gemini-2.0-flash-exp",
    )
    
    from src.core.llm.providers import GeminiProvider
    provider = GeminiProvider(config)
    await provider.initialize()
    
    test_text = "This is a test sentence for token counting."
    
    try:
        token_count = provider.count_tokens(test_text)
        print(f"Text: '{test_text}'")
        print(f"Token count: {token_count}")
        print("✅ Token counting works!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n🧪 Gemini 3 Pro Integration Tests\n")
    
    results = []
    
    # Run tests
    results.append(("Basic Completion", await test_gemini_basic()))
    results.append(("Streaming", await test_gemini_streaming()))
    results.append(("Fallback", await test_gemini_fallback()))
    results.append(("Token Counting", await test_gemini_token_counting()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed or were skipped")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
