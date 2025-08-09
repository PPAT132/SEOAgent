import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import './index.css';

export default function App() {
  const [html, setHtml] = useState('');
  const [diff, setDiff] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleGenerate = async () => {
    setIsLoading(true);
    setDiff('🔄 Optimizing HTML... Please wait...');
    
    try {
      const res = await fetch('http://127.0.0.1:8000/optimizev1', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ html }),
      });
      const data = await res.json();
      setDiff(data.diff || '// No diff returned');
    } catch (err) {
      console.error(err);
      setDiff('// Error: cannot reach backend');
    } finally {
      setIsLoading(false);
    }
  };
  const handleDownload = () => {
    if (!diff) return;
    const blob = new Blob([diff], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'patch.diff';
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
      className="min-h-screen flex flex-col bg-gradient-to-br from-purple-600 via-indigo-600 to-blue-600 text-white font-sans"
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
            SEO Agent Playground
          </h1>
          <Link 
            to="/lighthouse" 
            className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors backdrop-blur-sm"
          >
            🔍 Lighthouse Raw Data →
          </Link>
        </div>
      </motion.header>

      {/* Main */}
      <motion.main
        className="flex flex-1 flex-col md:flex-row p-4 gap-4 overflow-hidden"
        variants={sectionVariants}
      >
        <motion.textarea
          id="html-in"
          className="flex-1 min-h-[200px] md:min-h-0 p-4 rounded-lg bg-black/40 border border-white/20 focus:outline-none focus:ring-2 focus:ring-violet-400 resize-none font-mono placeholder:text-gray-300 backdrop-blur-lg"
          placeholder="Paste raw HTML here..."
          value={html}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setHtml(e.target.value)}
          whileFocus={{ scale: 1.01 }}
        />
        <motion.textarea
          id="diff-out"
          className="flex-1 min-h-[200px] md:min-h-0 p-4 rounded-lg bg-black/20 border border-white/20 focus:outline-none focus:ring-2 focus:ring-sky-400 overflow-auto font-mono backdrop-blur-lg resize-none"
          value={diff}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setDiff(e.target.value)}
          variants={sectionVariants}
          whileFocus={{ scale: 1.01 }}
        />
      </motion.main>

      {/* Buttons */}
      <motion.footer
        className="py-4 bg-white/10 backdrop-blur-sm shadow-inner flex flex-col md:flex-row justify-center gap-4"
        variants={sectionVariants}
      >
        <motion.button
          onClick={handleGenerate}
          disabled={isLoading}
          className={`px-6 py-3 rounded-full font-semibold shadow-lg transition-all ${
            isLoading 
              ? 'bg-gray-500 cursor-not-allowed' 
              : 'bg-gradient-to-r from-green-400 to-emerald-600 hover:brightness-110'
          }`}
          whileHover={isLoading ? {} : { scale: 1.05 }}
          whileTap={isLoading ? {} : { scale: 0.95 }}
        >
          {isLoading ? '🔄 Generating...' : 'Generate Patch'}
        </motion.button>
        <motion.button
          onClick={handleDownload}
          className="px-6 py-3 rounded-full bg-gradient-to-r from-sky-400 to-indigo-600 hover:brightness-110 transition-shadow shadow-lg font-semibold"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          Apply & Download
        </motion.button>
      </motion.footer>
    </motion.div>
  );
}
