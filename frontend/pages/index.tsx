import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { motion } from 'framer-motion';
import IntroAnimation from '../components/IntroAnimation';
import { useState } from 'react';

export default function Home() {
  const router = useRouter();
  const [introDone, setIntroDone] = useState(false);

  return (
    <main style={{ background: '#050505', minHeight: '100vh', color: 'white', fontFamily: 'Inter, sans-serif', overflow: 'hidden' }}>
      {!introDone && <IntroAnimation onComplete={() => setIntroDone(true)} />}

      {introDone && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            justifyContent: 'center', minHeight: '100vh', padding: '40px 24px', textAlign: 'center',
          }}
        >
          {/* Glow orb */}
          <div style={{
            position: 'absolute', width: 500, height: 500, borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(108,99,255,0.15) 0%, transparent 70%)',
            top: '50%', left: '50%', transform: 'translate(-50%, -50%)', pointerEvents: 'none',
          }} />

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.7 }}
          >
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 8, padding: '6px 16px',
              borderRadius: 20, border: '1px solid rgba(108,99,255,0.3)',
              background: 'rgba(108,99,255,0.08)', marginBottom: 24,
              fontSize: 12, color: '#a89dff', letterSpacing: 1.2,
            }}>
              POWERED BY INSTANTID + ANIMATEDIFF
            </div>

            <h1 style={{
              fontSize: 'clamp(36px, 6vw, 72px)', fontWeight: 800, lineHeight: 1.1,
              marginBottom: 20, letterSpacing: -1,
              background: 'linear-gradient(135deg, #ffffff 30%, #6c63ff 70%)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}>
              Identity Generation<br />Studio
            </h1>

            <p style={{ fontSize: 18, color: '#606060', maxWidth: 520, marginBottom: 40, lineHeight: 1.7 }}>
              Generate photorealistic images and videos while preserving your face identity — tracked with Comet ML for full experiment lineage.
            </p>

            <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
              <motion.button
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => router.push('/studio')}
                style={{
                  padding: '14px 32px', borderRadius: 12, border: 'none',
                  background: 'linear-gradient(135deg, #6c63ff, #8b5cf6)',
                  color: 'white', fontSize: 16, fontWeight: 700, cursor: 'pointer',
                  boxShadow: '0 4px 24px rgba(108,99,255,0.4)',
                }}
              >
                Launch Studio &rarr;
              </motion.button>

              <motion.a
                whileHover={{ scale: 1.04 }}
                href="https://github.com/OmSapkar24/identity-gen-studio"
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  padding: '14px 32px', borderRadius: 12,
                  border: '1px solid rgba(108,99,255,0.3)',
                  background: 'transparent', color: '#a89dff',
                  fontSize: 16, fontWeight: 500, cursor: 'pointer',
                  textDecoration: 'none',
                }}
              >
                View on GitHub
              </motion.a>
            </div>
          </motion.div>

          {/* Feature grid */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.7 }}
            style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginTop: 80, maxWidth: 860, width: '100%' }}
          >
            {[
              { icon: '🧠', title: 'InstantID', desc: 'Face identity preservation across every generation' },
              { icon: '🎬', title: 'AnimateDiff + SVD', desc: 'Smooth, identity-consistent video generation' },
              { icon: '📊', title: 'Comet ML Tracking', desc: 'Hyperparameters, prompts and artifacts logged automatically' },
              { icon: '⚡', title: 'FastAPI Backend', desc: 'Async GPU inference with job queue' },
            ].map(f => (
              <div key={f.title} style={{
                padding: '20px', borderRadius: 16,
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid rgba(255,255,255,0.06)',
                backdropFilter: 'blur(10px)', textAlign: 'left',
              }}>
                <div style={{ fontSize: 28, marginBottom: 10 }}>{f.icon}</div>
                <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 6, color: '#e0e0e0' }}>{f.title}</div>
                <div style={{ fontSize: 13, color: '#505050', lineHeight: 1.6 }}>{f.desc}</div>
              </div>
            ))}
          </motion.div>
        </motion.div>
      )}
    </main>
  );
}
