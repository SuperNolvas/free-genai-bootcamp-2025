import React, { useState, useEffect } from 'react';
import OpenAI from 'openai';
import { KeyRound, Copy, Loader2, Eye, EyeOff } from 'lucide-react';

function App() {
  const [apiKey, setApiKey] = useState(() => {
    const savedKey = localStorage.getItem('openai_api_key');
    return savedKey || '';
  });
  const [showApiKey, setShowApiKey] = useState(false);
  const [category, setCategory] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Securely store API key in localStorage when it changes
  useEffect(() => {
    if (apiKey) {
      localStorage.setItem('openai_api_key', apiKey);
    } else {
      localStorage.removeItem('openai_api_key');
    }
  }, [apiKey]);

  const generateVocabulary = async () => {
    if (!apiKey) {
      setError('Please enter your OpenAI API key');
      return;
    }
    if (!category) {
      setError('Please enter a category');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const openai = new OpenAI({ apiKey, dangerouslyAllowBrowser: true });
      
      const prompt = `Generate a vocabulary list for the category '${category}' in Russian and English.
      Include 10 words or phrases. For each entry, provide:
      - The Russian word/phrase
      - English translation
      - Part of speech
      - Category
      
      Format the response as a JSON object with the structure shown in the example below:
      {
        "vocabulary": [
          {
            "russian": "привет",
            "english": "hello",
            "partOfSpeech": "interjection",
            "category": "greetings"
          }
        ]
      }`;

      const response = await openai.chat.completions.create({
        model: "gpt-3.5-turbo",
        messages: [
          {
            role: "system",
            content: "You are a helpful language learning assistant that generates vocabulary lists in JSON format."
          },
          {
            role: "user",
            content: prompt
          }
        ],
        temperature: 0.7
      });

      const content = response.choices[0].message.content;
      if (content) {
        const formattedJson = JSON.stringify(JSON.parse(content), null, 2);
        setResult(formattedJson);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(result);
      alert('Copied to clipboard!');
    } catch (err) {
      setError('Failed to copy to clipboard');
    }
  };

  const clearApiKey = () => {
    setApiKey('');
    setShowApiKey(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 p-6">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-6">📚 Vocabulary Importer</h1>
          
          <div className="space-y-6">
            {/* API Key Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                OpenAI API Key
              </label>
              <div className="relative">
                <input
                  type={showApiKey ? "text" : "password"}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-24"
                  placeholder="Enter your OpenAI API key"
                  autoComplete="off"
                  spellCheck="false"
                />
                <div className="absolute right-3 top-2.5 flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="text-gray-400 hover:text-gray-600 focus:outline-none"
                    title={showApiKey ? "Hide API Key" : "Show API Key"}
                  >
                    {showApiKey ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                  <KeyRound className="h-5 w-5 text-gray-400" />
                </div>
              </div>
              {apiKey && (
                <button
                  onClick={clearApiKey}
                  className="mt-2 text-sm text-red-600 hover:text-red-700"
                >
                  Clear API Key
                </button>
              )}
            </div>

            {/* Category Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Vocabulary Category
              </label>
              <input
                type="text"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., food, animals, professions"
              />
            </div>

            {/* Generate Button */}
            <button
              onClick={generateVocabulary}
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin mr-2 h-5 w-5" />
                  Generating...
                </>
              ) : (
                'Generate Vocabulary'
              )}
            </button>

            {/* Error Message */}
            {error && (
              <div className="text-red-600 text-sm mt-2">
                {error}
              </div>
            )}

            {/* Results */}
            {result && (
              <div className="mt-6">
                <div className="flex justify-between items-center mb-2">
                  <h2 className="text-lg font-semibold text-gray-800">Generated Vocabulary</h2>
                  <button
                    onClick={copyToClipboard}
                    className="flex items-center text-sm text-blue-600 hover:text-blue-700"
                  >
                    <Copy className="h-4 w-4 mr-1" />
                    Copy to Clipboard
                  </button>
                </div>
                <pre className="bg-gray-50 p-4 rounded-lg overflow-auto max-h-96">
                  <code className="text-sm">{result}</code>
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;