import GenerationCanvas from '../components/GenerationCanvas';
import { motion } from 'framer-motion';
import { useRouter } from 'next/router';

export default function StudioPage() {
  const router = useRouter();
  return (
    <div style={{ background: '#050505', minHeight: '100vh', fontFamily: 'Inter, sans-serif' }}>
      {/* Nav bar */}
      <motion.nav
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '14px 28px',
          background: 'rgba(5,5,5,0.85)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(255,255,255,0.05)',
        }}
      >
        <button
          onClick={() => router.push('/')}
          style={{
            background: 'none', border: 'none', color: '#a89dff',
            cursor: 'pointer', fontSize: 13, display: 'flex', alignItems: 'center', gap: 6,
          }}
        >
          &larr; Home
        </button>
        <span style={{
          fontSize: 14, fontWeight: 700,
          background: 'linear-gradient(135deg, #6c63ff, #8b5cf6)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        }}>
          Identity Gen Studio
        </span>
        <a
          href="https://github.com/OmSapkar24/identity-gen-studio"
          target="_blank"
          rel="noopener noreferrer"
          style={{ fontSize: 12, color: '#404040', textDecoration: 'none' }}
        >
          GitHub
        </a>
      </motion.nav>

      {/* Main canvas padded below nav */}
      <div style={{ paddingTop: 60 }}>
        <GenerationCanvas />
      </div>
    </div>
  );
}
