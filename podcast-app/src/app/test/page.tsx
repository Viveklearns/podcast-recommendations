'use client';

import { useState, useEffect } from 'react';

export default function TestPage() {
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function testAPI() {
      try {
        console.log('Testing API connection...');

        // Test 1: Fetch stats
        const statsResponse = await fetch('http://localhost:8000/api/stats');
        console.log('Stats response:', statsResponse.status);
        const stats = await statsResponse.json();

        // Test 2: Fetch recommendations
        const recsResponse = await fetch('http://localhost:8000/api/recommendations?limit=5');
        console.log('Recommendations response:', recsResponse.status);
        const recs = await recsResponse.json();

        setResult({
          stats,
          recommendations: recs,
          success: true
        });
      } catch (err) {
        console.error('API Test Error:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    }

    testAPI();
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">API Connection Test</h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
          <strong>Success!</strong> API is working
        </div>
      )}

      <div className="bg-gray-100 p-4 rounded">
        <h2 className="font-bold mb-2">Result:</h2>
        <pre className="text-xs overflow-auto">
          {JSON.stringify(result || error, null, 2)}
        </pre>
      </div>
    </div>
  );
}
