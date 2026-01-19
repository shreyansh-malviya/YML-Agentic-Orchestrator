# Grok (xAI) Integration Guide

## Overview

Grok is xAI's advanced language model with real-time knowledge and analytical capabilities. This integration allows you to use Grok models in your agent workflows alongside other LLMs like Gemini, GPT-4, and Claude.

## Setup

### 1. Get Your API Key

1. Visit [console.x.ai](https://console.x.ai/)
2. Sign up or log in to your xAI account
3. Navigate to API Keys section
4. Create a new API key

### 2. Configure Environment

Add your Grok API key to `.env`:

```bash
XAI_API_KEY=your_xai_api_key_here
```

### 3. Install Dependencies

Grok uses the OpenAI-compatible API, so ensure you have the OpenAI package installed:

```bash
pip install openai
```

## Available Models

### Current Grok Models

- **grok-beta** - Latest beta version with cutting-edge features
- **grok-2-latest** - Stable Grok 2 model
- **grok-2-vision-1212** - Grok with vision capabilities
- **grok-vision-beta** - Beta vision model

> **Note**: Model availability may change. Check [xAI documentation](https://docs.x.ai/) for the latest models.

## Usage in Workflows

### Basic Configuration

```yaml
agents:
  - id: "research_agent"
    role: "Research Assistant"
    goal: "Research topics with real-time knowledge"
    model: grok-beta
    instruction: |
      Use your real-time knowledge to provide accurate insights.
```

### With Custom Settings

```yaml
agents:
  - id: "analyst_agent"
    role: "Data Analyst"
    goal: "Analyze data with Grok"
    model: grok-2-latest
    instruction: |
      Analyze the data and provide insights.

models:
  grok-2-latest:
    provider: xai
    model: grok-2-latest
    temperature: 0.5 # Lower for more focused responses
    max_tokens: 4096
```

### Multi-LLM Workflows

Compare outputs from different models:

```yaml
agents:
  - id: "grok_analyst"
    model: grok-beta

  - id: "gemini_analyst"
    model: gemini-2.5-flash

  - id: "consolidator"
    model: grok-2-latest
    instruction: |
      Compare insights from Grok and Gemini agents.
      Synthesize the best findings from both.

workflow:
  type: parallel
  branches:
    - grok_analyst
    - gemini_analyst
  then: consolidator
```

## Model Configuration Options

```yaml
models:
  grok-beta:
    provider: xai # Provider identifier
    model: grok-beta # Specific model name
    temperature: 0.7 # Creativity (0.0-1.0)
    max_tokens: 8096 # Maximum response length
```

### Temperature Guidelines

- **0.0-0.3**: Highly focused, deterministic (good for analysis, code)
- **0.4-0.7**: Balanced creativity and focus (general use)
- **0.8-1.0**: More creative and diverse (brainstorming, creative writing)

## Features & Capabilities

### Real-Time Knowledge

Grok has access to real-time information, making it excellent for:

- Current events research
- Up-to-date technical documentation
- Market analysis
- News summarization

### Analytical Capabilities

Strong performance in:

- Data analysis
- Code generation and review
- Complex reasoning tasks
- Multi-step problem solving

### Vision Models

For vision-enabled models (like `grok-vision-beta`):

- Image analysis (coming soon in workflow support)
- Chart and diagram interpretation
- Visual data extraction

## Examples

### Example 1: Research Workflow

```yaml
agents:
  - id: "grok_researcher"
    role: "Research Agent"
    goal: "Research latest AI developments"
    model: grok-beta
    instruction: |
      Research the latest developments in AI and machine learning.
      Focus on breakthroughs from the past month.
      Provide sources and dates.

workflow:
  type: sequential
  steps:
    - grok_researcher
```

### Example 2: Parallel Analysis

```yaml
agents:
  - id: "grok_analyzer"
    role: "Grok Analyst"
    model: grok-2-latest

  - id: "gemini_analyzer"
    role: "Gemini Analyst"
    model: gemini-2.5-flash

  - id: "synthesizer"
    role: "Synthesis Agent"
    model: grok-beta
    instruction: |
      Compare the analyses from both agents.
      Identify agreements and disagreements.
      Provide a synthesized conclusion.

workflow:
  type: parallel
  branches:
    - grok_analyzer
    - gemini_analyzer
  then: synthesizer
```

## Best Practices

### 1. Choose the Right Model

- **grok-beta**: Latest features, may be less stable
- **grok-2-latest**: Production-ready, stable performance
- **grok-vision-\***: When you need image understanding

### 2. Optimize Prompts

Grok responds well to:

- Clear, specific instructions
- Structured output requests
- Context about the task goals

### 3. Handle Rate Limits

```python
# Grok has different rate limits than other providers
# Check your console for current limits
# Implement retries if needed
```

### 4. Cost Management

- Monitor your usage at [console.x.ai](https://console.x.ai/)
- Use appropriate max_tokens to control costs
- Consider using lower-cost models for simpler tasks

## Troubleshooting

### Error: XAI_API_KEY not found

**Solution**: Ensure `.env` file has:

```bash
XAI_API_KEY=your_actual_key_here
```

### Error: openai package not installed

**Solution**: Install the OpenAI package:

```bash
pip install openai
```

### Error: Rate limit exceeded

**Solution**:

- Wait for rate limit reset
- Reduce request frequency
- Upgrade your xAI plan

### Error: Model not found

**Solution**:

- Check [xAI docs](https://docs.x.ai/) for available models
- Verify model name spelling
- Some models may require beta access

## API Reference

### grok_response()

```python
def grok_response(prompt: str, model_config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get response from xAI Grok model.

    Args:
        prompt: The input prompt
        model_config: Model configuration with:
            - model: Model name (default: 'grok-beta')
            - temperature: 0.0-1.0 (default: 0.7)
            - max_tokens: Maximum tokens (default: 8096)

    Returns:
        Response string from Grok
    """
```

### Automatic Routing

The system automatically routes requests to Grok when model name contains:

- `grok`
- `xai`

Example:

```yaml
model: grok-beta      # ✓ Routes to Grok
model: grok-2-latest  # ✓ Routes to Grok
model: xai-grok       # ✓ Routes to Grok
```

## Additional Resources

- **xAI Console**: https://console.x.ai/
- **API Documentation**: https://docs.x.ai/
- **Pricing**: https://x.ai/pricing
- **Community**: https://discord.gg/xai (if available)

## Example Files

Check these example configurations:

- `engine/examples/config_grok_example.yml` - Basic Grok usage
- `engine/examples/config_sequential.yml` - Sequential workflow pattern
- `engine/examples/config_parallel_mcp.yml` - Parallel with MCP tools

## Next Steps

1. Get your API key from console.x.ai
2. Add it to your .env file
3. Try the example: `python main.py --file engine/examples/config_grok_example.yml`
4. Experiment with different models and temperatures
5. Integrate Grok into your multi-LLM workflows
