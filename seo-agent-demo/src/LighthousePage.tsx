import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

export default function LighthousePage() {
  const [html, setHtml] = useState('');
  const [result, setResult] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!html.trim()) {
      setResult('Please enter some HTML content to analyze.');
      return;
    }

    setIsLoading(true);
    setResult('🔄 Analyzing HTML with Lighthouse...');

    try {
      const res = await fetch('http://127.0.0.1:8000/lighthouse-raw', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ html }),
      });
      
      const data = await res.json();
      
      // Display the raw JSON for you to see the structure
      setResult(JSON.stringify(data, null, 2));
      
    } catch (err) {
      console.error('Lighthouse analysis error:', err);
      setResult('❌ Error: Cannot reach Lighthouse backend service');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    if (!result) return;
    const blob = new Blob([result], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'lighthouse-raw-data.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  // Animation variants
  const containerVariants = {
    initial: { opacity: 0 },
    animate: {
      opacity: 1,
      transition: {
        when: 'beforeChildren',
        staggerChildren: 0.15,
      },
    },
  } as const;

  const sectionVariants = {
    initial: { y: 40, opacity: 0 },
    animate: { y: 0, opacity: 1, transition: { type: 'spring', stiffness: 80 } },
  } as const;

  return (
    <motion.div
      className="min-h-screen flex flex-col bg-gradient-to-br from-blue-600 via-cyan-600 to-teal-600 text-white font-sans"
      variants={containerVariants}
      initial="initial"
      animate="animate"
    >
      {/* Header */}
      <motion.header
        className="py-4 shadow-md backdrop-blur-sm bg-white/10"
        variants={sectionVariants}
      >
        <div className="flex justify-between items-center px-4">
          <h1 className="text-3xl md:text-4xl font-bold uppercase tracking-wide drop-shadow-lg">
            🔍 Lighthouse Raw Data
          </h1>
          <Link 
            to="/optimizer" 
            className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors backdrop-blur-sm"
          >
            ← Back to Optimizer
          </Link>
        </div>
      </motion.header>

      {/* Main */}
      <motion.main
        className="flex flex-1 flex-col md:flex-row p-4 gap-4 overflow-hidden"
        variants={sectionVariants}
      >
        {/* HTML Input */}
        <motion.div className="flex-1 flex flex-col">
          <label className="text-lg font-semibold mb-2">📝 HTML Input:</label>
          <motion.textarea
            className="flex-1 min-h-[200px] md:min-h-0 p-4 rounded-lg bg-black/40 border border-white/20 focus:outline-none focus:ring-2 focus:ring-cyan-400 resize-none font-mono placeholder:text-gray-300 backdrop-blur-lg"
            placeholder="Paste your HTML code here for Lighthouse analysis..."
            value={html}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setHtml(e.target.value)}
            whileFocus={{ scale: 1.01 }}
          />
        </motion.div>

        {/* Raw JSON Output */}
        <motion.div className="flex-1 flex flex-col">
          <label className="text-lg font-semibold mb-2">📊 Raw Lighthouse JSON:</label>
          <motion.textarea
            className="flex-1 min-h-[200px] md:min-h-0 p-4 rounded-lg bg-black/20 border border-white/20 focus:outline-none focus:ring-2 focus:ring-teal-400 overflow-auto font-mono backdrop-blur-lg resize-none text-xs"
            value={isLoading ? '🔄 Analyzing with Lighthouse... Please wait...' : result}
            readOnly
            variants={sectionVariants}
            whileFocus={{ scale: 1.01 }}
          />
        </motion.div>
      </motion.main>

      {/* Buttons */}
      <motion.footer
        className="py-4 bg-white/10 backdrop-blur-sm shadow-inner flex flex-col md:flex-row justify-center gap-4"
        variants={sectionVariants}
      >
        <motion.button
          onClick={handleAnalyze}
          disabled={isLoading}
          className={`px-6 py-3 rounded-full font-semibold shadow-lg transition-all ${
            isLoading 
              ? 'bg-gray-500 cursor-not-allowed' 
              : 'bg-gradient-to-r from-cyan-400 to-blue-600 hover:brightness-110'
          }`}
          whileHover={isLoading ? {} : { scale: 1.05 }}
          whileTap={isLoading ? {} : { scale: 0.95 }}
        >
          {isLoading ? '🔄 Analyzing...' : '🔍 Get Raw Lighthouse Data'}
        </motion.button>
        
        <motion.button
          onClick={handleDownload}
          className="px-6 py-3 rounded-full bg-gradient-to-r from-teal-400 to-green-600 hover:brightness-110 transition-shadow shadow-lg font-semibold"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          📄 Download JSON
        </motion.button>
      </motion.footer>
    </motion.div>
  );
}
