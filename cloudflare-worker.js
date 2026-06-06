// Cloudflare Worker for MCDA Chatbot
// Deploy this to Cloudflare Workers to securely proxy AI requests
// Your API key stays server-side - never exposed to the client

export default {
	async fetch(request, env, ctx) {
		// Handle CORS preflight
		if (request.method === 'OPTIONS') {
			return handleCORS();
		}

		// Only allow POST requests
		if (request.method !== 'POST') {
			return new Response(JSON.stringify({ error: 'Method not allowed' }), {
				status: 405,
				headers: { 'Content-Type': 'application/json', ...corsHeaders() }
			});
		}

		try {
			const { message } = await request.json();

			if (!message || typeof message !== 'string') {
				return new Response(JSON.stringify({ error: 'Invalid message' }), {
					status: 400,
					headers: { 'Content-Type': 'application/json', ...corsHeaders() }
				});
			}

			// Call Cloudflare Workers AI (or your preferred AI service)
			const aiResponse = await callAI(message, env);

			return new Response(JSON.stringify({ response: aiResponse }), {
				status: 200,
				headers: { 'Content-Type': 'application/json', ...corsHeaders() }
			});
		} catch (error) {
			console.error('Worker error:', error);
			return new Response(JSON.stringify({ error: 'Internal server error' }), {
				status: 500,
				headers: { 'Content-Type': 'application/json', ...corsHeaders() }
			});
		}
	}
};

function corsHeaders() {
	return {
		'Access-Control-Allow-Origin': '*', // Or restrict to your domain: 'https://madisonchinesedance.github.io'
		'Access-Control-Allow-Methods': 'POST, OPTIONS',
		'Access-Control-Allow-Headers': 'Content-Type',
	};
}

function handleCORS() {
	return new Response(null, {
		status: 204,
		headers: corsHeaders()
	});
}

async function callAI(message, env) {
	// ============================================
	// OPTION 1: Cloudflare Workers AI (recommended)
	// Uses built-in models like @cf/meta/llama-3.1-8b-instruct
	// No external API key needed - uses your Cloudflare account
	// ============================================
	if (env.AI) {
		const response = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
			messages: [
				{
					role: 'system',
					content: `You are the MCDA Assistant for the Madison Chinese Dance Academy. 
					You help visitors with questions about:
					- Classes and programs (classical Chinese dance, folk dance, etc.)
					- Upcoming performances and events
					- Ticket purchases
					- Donations and support
					- Academy history and mission
					- Community involvement
					Keep responses helpful, friendly, and concise. If you don't know something, 
					suggest they visit the website or contact the academy directly.`
				},
				{ role: 'user', content: message }
			],
			max_tokens: 500,
			temperature: 0.7
		});
		return response.response || response.text || 'Sorry, I could not generate a response.';
	}

	// ============================================
	// OPTION 2: External API (OpenAI, Anthropic, etc.)
	// Store your API key in Cloudflare Worker secrets (not in code!)
	// ============================================
	if (env.OPENAI_API_KEY) {
		const response = await fetch('https://api.openai.com/v1/chat/completions', {
			method: 'POST',
			headers: {
				'Authorization': `Bearer ${env.OPENAI_API_KEY}`,
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				model: 'gpt-4o-mini',
				messages: [
					{
						role: 'system',
						content: 'You are the MCDA Assistant for the Madison Chinese Dance Academy...'
					},
					{ role: 'user', content: message }
				],
				max_tokens: 500,
				temperature: 0.7
			})
		});
		const data = await response.json();
		return data.choices?.[0]?.message?.content || 'Sorry, I could not generate a response.';
	}

	// ============================================
	// OPTION 3: Anthropic Claude
	// ============================================
	if (env.ANTHROPIC_API_KEY) {
		const response = await fetch('https://api.anthropic.com/v1/messages', {
			method: 'POST',
			headers: {
				'x-api-key': env.ANTHROPIC_API_KEY,
				'anthropic-version': '2023-06-01',
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				model: 'claude-3-haiku-20240307',
				max_tokens: 500,
				system: 'You are the MCDA Assistant for the Madison Chinese Dance Academy...',
				messages: [{ role: 'user', content: message }]
			})
		});
		const data = await response.json();
		return data.content?.[0]?.text || 'Sorry, I could not generate a response.';
	}

	// Fallback if no AI service configured
	return 'Chatbot is not configured. Please set up Cloudflare Workers AI or add an API key to the Worker secrets.';
}