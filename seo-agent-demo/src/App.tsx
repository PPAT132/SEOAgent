import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import './index.css';

interface SEOAnalysisResult {
  seo_score: number;
  total_lines: number;
  issues: Array<{
    title: string;
    raw_html: string;
    optimized_html: string;
    ranges?: number[][];
  }>;
  context: string;
}

interface OptimizationResult {
  success: boolean;
  modified_html?: string;
  optimization_result?: SEOAnalysisResult;
  original_seo_score?: number;
  optimized_seo_score?: number;
  issues_processed?: number;
  error?: string;
}

export default function App() {
  const [html, setHtml] = useState('');
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isOriginalCollapsed, setIsOriginalCollapsed] = useState(false);
  const [isOptimizedCollapsed, setIsOptimizedCollapsed] = useState(false);

  const handleGenerate = async () => {
    setIsLoading(true);
    setOptimizationResult(null);
    
    try {
      const res = await fetch('http://127.0.0.1:3001/optimizev1', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ html }),
      });
      const data: OptimizationResult = await res.json();
      
      // Check if it's an error response
      if (data.error) {
        setOptimizationResult({
          success: false,
          error: data.error
        });
        return;
      }
      
      setOptimizationResult(data);
    } catch (err) {
      console.error(err);
      setOptimizationResult({
        success: false,
        error: 'Cannot reach backend'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    if (!optimizationResult?.modified_html) return;
    const blob = new Blob([optimizationResult.modified_html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'optimized.html';
    a.click();
    URL.revokeObjectURL(url);
  };

  const renderSEOComparison = () => {
    if (!optimizationResult) return null;

    const originalScore = optimizationResult.original_seo_score || 0;
    const optimizedScore = optimizationResult.optimized_seo_score || 0;
    const improvement = optimizedScore - originalScore;
    const improvementPercent = originalScore > 0 ? (improvement / originalScore * 100) : 0;

    return (
      <motion.div 
        className="bg-black/30 rounded-lg p-6 backdrop-blur-lg border border-white/20"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <h2 className="text-2xl font-bold mb-4 text-center">SEO Score Comparison</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Original Score */}
          <div className="bg-red-500/20 rounded-lg p-4 border border-red-400/30">
            <h3 className="text-lg font-semibold text-red-300 mb-2">Before Optimization</h3>
            <div className="text-3xl font-bold text-red-400 mb-2">{originalScore}/100</div>
            <div className="text-sm text-red-300">
              Issues found: {optimizationResult.optimization_result?.issues.length || 0}
            </div>
          </div>

          {/* Optimized Score */}
          <div className="bg-green-500/20 rounded-lg p-4 border border-green-400/30">
            <h3 className="text-lg font-semibold text-green-300 mb-2">After Optimization</h3>
            <div className="text-3xl font-bold text-green-400 mb-2">{optimizedScore}/100</div>
            <div className="text-sm text-green-300">
              Issues processed: {optimizationResult.issues_processed || 0}
            </div>
          </div>
        </div>

        {/* Improvement */}
        <div className="mt-4 text-center">
          <div className={`text-lg font-semibold ${improvement >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {improvement >= 0 ? '+' : ''}{improvement} points ({improvementPercent >= 0 ? '+' : ''}{improvementPercent.toFixed(1)}%)
          </div>
        </div>
      </motion.div>
    );
  };

  const renderIssuesList = () => {
    if (!optimizationResult?.optimization_result?.issues) return null;

    return (
      <motion.div 
        className="bg-black/30 rounded-lg p-6 backdrop-blur-lg border border-white/20"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <h2 className="text-2xl font-bold mb-4">Issues Found & Fixed</h2>
        <div className="space-y-3 max-h-60 overflow-y-auto">
          {optimizationResult.optimization_result.issues.map((issue, index) => (
            <div key={index} className="bg-white/10 rounded-lg p-3">
              <div className="font-semibold text-yellow-300">{issue.title}</div>
              <div className="text-sm text-gray-300 mt-1">
                Ranges: {issue.ranges ? JSON.stringify(issue.ranges) : 'No ranges'}
              </div>
              <div className="text-xs text-gray-400 mt-1">
                Original: {issue.raw_html.substring(0, 50)}...
              </div>
              <div className="text-xs text-green-400 mt-1">
                Fixed: {issue.optimized_html.substring(0, 50)}...
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    );
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
        className="flex flex-1 flex-col p-4 gap-4"
        variants={sectionVariants}
      >
        {/* Input Section */}
        <motion.div className="flex flex-col md:flex-row gap-4" variants={sectionVariants}>
          <div className="flex-1">
            <div className="bg-black/30 rounded-lg backdrop-blur-lg border border-white/20">
              <button
                onClick={() => setIsOriginalCollapsed(!isOriginalCollapsed)}
                className="w-full p-4 text-left flex items-center justify-between hover:bg-white/10 transition-colors"
              >
                <h3 className="text-lg font-semibold">📝 Original HTML</h3>
                <motion.div
                  animate={{ rotate: isOriginalCollapsed ? 0 : 180 }}
                  transition={{ duration: 0.2 }}
                  className="text-xl"
                >
                  ▼
                </motion.div>
              </button>
              
              <div className={isOriginalCollapsed ? 'h-[200px] overflow-y-auto' : 'overflow-visible'}>
                <motion.textarea
                  id="html-in"
                  className="w-full min-h-[200px] p-4 rounded-lg bg-black/40 border border-white/20 focus:outline-none focus:ring-2 focus:ring-violet-400 font-mono placeholder:text-gray-300 backdrop-blur-lg"
                  placeholder="Paste raw HTML here..."
                  value={html}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setHtml(e.target.value)}
                  whileFocus={{ scale: 1.01 }}
                />
              </div>
            </div>
          </div>

          <div className="flex-1">
            <div className="bg-black/30 rounded-lg backdrop-blur-lg border border-white/20">
              <button
                onClick={() => setIsOptimizedCollapsed(!isOptimizedCollapsed)}
                className="w-full p-4 text-left flex items-center justify-between hover:bg-white/10 transition-colors"
              >
                <h3 className="text-lg font-semibold">✨ Optimized HTML</h3>
                <motion.div
                  animate={{ rotate: isOptimizedCollapsed ? 0 : 180 }}
                  transition={{ duration: 0.2 }}
                  className="text-xl"
                >
                  ▼
                </motion.div>
              </button>
              
              <div className={isOptimizedCollapsed ? 'h-[200px] overflow-y-auto' : ''}>
                <div className="min-h-[200px] p-4 rounded-lg bg-black/20 border border-white/20 backdrop-blur-lg overflow-auto">
                  {optimizationResult?.modified_html ? (
                    <pre className="text-sm font-mono text-green-300 whitespace-pre-wrap">
                      {optimizationResult.modified_html}
                    </pre>
                  ) : (
                    <div className="text-gray-400 text-center mt-8">
                      {isLoading ? '🔄 Optimizing...' : 'Optimized HTML will appear here'}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* SEO Comparison Section */}
        {optimizationResult && renderSEOComparison()}

        {/* Issues List Section */}
        {optimizationResult && renderIssuesList()}

        {/* Error Display */}
        {optimizationResult?.error && (
          <motion.div 
            className="bg-red-500/20 rounded-lg p-4 border border-red-400/30"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="text-red-300 font-semibold">Error:</div>
            <div className="text-red-400">{optimizationResult.error}</div>
          </motion.div>
        )}
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
          {isLoading ? '🔄 Optimizing...' : '🚀 Optimize SEO'}
        </motion.button>
        <motion.button
          onClick={handleDownload}
          disabled={!optimizationResult?.modified_html}
          className={`px-6 py-3 rounded-full font-semibold shadow-lg transition-all ${
            !optimizationResult?.modified_html
              ? 'bg-gray-500 cursor-not-allowed'
              : 'bg-gradient-to-r from-sky-400 to-indigo-600 hover:brightness-110'
          }`}
          whileHover={!optimizationResult?.modified_html ? {} : { scale: 1.05 }}
          whileTap={!optimizationResult?.modified_html ? {} : { scale: 0.95 }}
        >
          💾 Download Optimized HTML
        </motion.button>
      </motion.footer>
    </motion.div>
  );
}
