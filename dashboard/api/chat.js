// Vercel Serverless Function for LLM Chat
// Supports OpenRouter and DeepSeek APIs

const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY;

// Expert role configurations with specialized system prompts
const EXPERT_CONFIGS = {
  architect: {
    name: 'ARCHI',
    model: 'openrouter', // Uses OpenRouter for complex reasoning
    systemPrompt: `You are ARCHI, a senior systems architect AI expert in the TinyRecursiveModels swarm. 
You specialize in system design, architecture patterns, scalability, and high-level technical decisions.
Respond concisely and technically. Use LCARS-style formatting when appropriate.
Your responses should reflect deep expertise in distributed systems, microservices, and AI infrastructure.`,
  },
  developer: {
    name: 'DEVO',
    model: 'deepseek', // Uses DeepSeek for code-focused tasks
    systemPrompt: `You are DEVO, a senior developer AI expert in the TinyRecursiveModels swarm.
You specialize in code implementation, debugging, optimization, and best practices.
Provide practical, working code solutions. Be concise but thorough.
Focus on clean code, performance, and maintainability.`,
  },
  analyst: {
    name: 'ANALYST',
    model: 'deepseek',
    systemPrompt: `You are ANALYST, a data analysis AI expert in the TinyRecursiveModels swarm.
You specialize in data patterns, metrics interpretation, and analytical insights.
Provide data-driven recommendations and identify patterns in complex information.`,
  },
  security: {
    name: 'SENTINEL',
    model: 'openrouter',
    systemPrompt: `You are SENTINEL, a security specialist AI expert in the TinyRecursiveModels swarm.
You specialize in security auditing, threat modeling, and secure system design.
Identify vulnerabilities and provide security-focused recommendations.`,
  },
  researcher: {
    name: 'SCRIBE',
    model: 'openrouter',
    systemPrompt: `You are SCRIBE, a research and documentation AI expert in the TinyRecursiveModels swarm.
You specialize in knowledge synthesis, documentation, and research compilation.
Provide well-structured, comprehensive information and documentation.`,
  },
};

async function callOpenRouter(messages, systemPrompt) {
  const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': 'https://tinyrecursivemodels.vercel.app',
      'X-Title': 'TinyRecursiveModels Dashboard',
    },
    body: JSON.stringify({
      model: 'deepseek/deepseek-chat-v3-0324',
      messages: [
        { role: 'system', content: systemPrompt },
        ...messages,
      ],
      max_tokens: 1024,
      temperature: 0.7,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`OpenRouter API error: ${response.status} - ${error}`);
  }

  return response.json();
}

async function callDeepSeek(messages, systemPrompt) {
  const response = await fetch('https://api.deepseek.com/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${DEEPSEEK_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'deepseek-chat',
      messages: [
        { role: 'system', content: systemPrompt },
        ...messages,
      ],
      max_tokens: 1024,
      temperature: 0.7,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`DeepSeek API error: ${response.status} - ${error}`);
  }

  return response.json();
}

export default async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { role, message, history = [] } = req.body;

    if (!role || !message) {
      return res.status(400).json({ error: 'Missing role or message' });
    }

    const expertConfig = EXPERT_CONFIGS[role];
    if (!expertConfig) {
      return res.status(400).json({ error: `Unknown role: ${role}` });
    }

    // Build message history for context
    const messages = [
      ...history.slice(-6).map(msg => ({
        role: msg.sender === 'user' ? 'user' : 'assistant',
        content: msg.text,
      })),
      { role: 'user', content: message },
    ];

    let result;
    const startTime = Date.now();

    if (expertConfig.model === 'openrouter' && OPENROUTER_API_KEY) {
      result = await callOpenRouter(messages, expertConfig.systemPrompt);
    } else if (expertConfig.model === 'deepseek' && DEEPSEEK_API_KEY) {
      result = await callDeepSeek(messages, expertConfig.systemPrompt);
    } else if (DEEPSEEK_API_KEY) {
      // Fallback to DeepSeek if OpenRouter not available
      result = await callDeepSeek(messages, expertConfig.systemPrompt);
    } else if (OPENROUTER_API_KEY) {
      // Fallback to OpenRouter if DeepSeek not available
      result = await callOpenRouter(messages, expertConfig.systemPrompt);
    } else {
      return res.status(500).json({ error: 'No LLM API keys configured' });
    }

    const responseTime = Date.now() - startTime;
    const responseText = result.choices?.[0]?.message?.content || 'No response generated';

    return res.status(200).json({
      response: responseText,
      name: expertConfig.name,
      role: role,
      reasoning_trace: `${expertConfig.model.toUpperCase()} > INFERENCE > ${responseTime}ms`,
      model: result.model || expertConfig.model,
      usage: result.usage,
    });

  } catch (error) {
    console.error('Chat API Error:', error);
    return res.status(500).json({
      error: error.message,
      response: `[NEURAL_LINK_ERROR] ${error.message}`,
      name: 'SYSTEM',
    });
  }
}
