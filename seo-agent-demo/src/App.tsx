import { useState } from 'react';
import './index.css';

export default function App() {
  const [html, setHtml] = useState('');
  const [diff, setDiff] = useState('');

  const handleGenerate = () => {
    // TODO: connect to backend /optimize
    console.log('Generate Patch clicked');
    setDiff('// diff will appear here');
  };

  const handleDownload = () => {
    // TODO: implement download of .patch file
    console.log('Apply & Download clicked');
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-purple-600 via-indigo-600 to-blue-600 text-white font-sans">
      {/* Header */}
      <header className="py-4 shadow-md backdrop-blur-sm bg-white/10">
        <h1 className="text-3xl md:text-4xl font-bold text-center uppercase tracking-wide">
          SEO Agent Playground
        </h1>
      </header>

      {/* Main */}
      <main className="flex flex-1 flex-col md:flex-row p-4 gap-4 overflow-hidden">
        <textarea
          id="html-in"
          className="flex-1 min-h-[200px] md:min-h-0 p-4 rounded-lg bg-black/40 border border-white/20 focus:outline-none focus:ring-2 focus:ring-violet-400 resize-none font-mono placeholder:text-gray-300 backdrop-blur-lg"
          placeholder="Paste raw HTML here..."
          value={html}
          onChange={(e) => setHtml(e.target.value)}
        />
        <pre
          id="diff-out"
          className="flex-1 min-h-[200px] md:min-h-0 p-4 rounded-lg bg-black/20 border border-white/20 overflow-auto font-mono backdrop-blur-lg whitespace-pre-wrap"
        >
          {diff}
        </pre>
      </main>

      {/* Buttons */}
      <footer className="py-4 bg-white/10 backdrop-blur-sm shadow-inner flex flex-col md:flex-row justify-center gap-4">
        <button
          onClick={handleGenerate}
          className="px-6 py-3 rounded-full bg-gradient-to-r from-green-400 to-emerald-600 hover:brightness-110 active:scale-95 transition-transform shadow-lg font-semibold"
        >
          Generate Patch
        </button>
        <button
          onClick={handleDownload}
          className="px-6 py-3 rounded-full bg-gradient-to-r from-sky-400 to-indigo-600 hover:brightness-110 active:scale-95 transition-transform shadow-lg font-semibold"
        >
          Apply & Download
        </button>
      </footer>
    </div>
  );
}
