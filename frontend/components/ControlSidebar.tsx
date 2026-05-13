'use client';
import { motion } from 'framer-motion';

interface Params {
  prompt: string;
  mode: 'image' | 'video';
  cfg_scale: number;
  seed: number;
  motion_bucket_id: number;
  steps: number;
}

interface Props {
  params: Params;
  setParams: (fn: (p: Params) => Params) => void;
  onClose: () => void;
}

const labelStyle = { fontSize: 12, color: '#808080', marginBottom: 4, display: 'block' as const };
const inputStyle = {
  width: '100%', padding: '8px 12px', borderRadius: 8,
  background: 'rgba(255,255,255,0.04)', border: '1px solid #2a2a2a',
  color: 'white', fontSize: 13, outline: 'none', boxSizing: 'border-box' as const,
};

export default function ControlSidebar({ params, setParams, onClose }: Props) {
  return (
    <motion.aside
      style={{
        width: 280, height: '100vh', background: 'rgba(10,10,10,0.95)',
        borderRight: '1px solid rgba(108,99,255,0.15)',
        backdropFilter: 'blur(20px)', padding: '24px 20px',
        display: 'flex', flexDirection: 'column', gap: 20, overflowY: 'auto',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
        <span style={{ fontSize: 14, fontWeight: 700, color: '#a89dff' }}>Advanced Settings</span>
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={onClose}
          style={{ background: 'none', border: 'none', color: '#606060', cursor: 'pointer', fontSize: 18, lineHeight: 1 }}
        >
          &times;
        </motion.button>
      </div>

      {/* CFG Scale */}
      <div>
        <label style={labelStyle}>CFG Scale &mdash; {params.cfg_scale}</label>
        <input
          type="range" min={1} max={20} step={0.5}
          value={params.cfg_scale}
          onChange={e => setParams(p => ({ ...p, cfg_scale: parseFloat(e.target.value) }))}
          style={{ width: '100%', accentColor: '#6c63ff' }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#404040' }}>
          <span>1</span><span>20</span>
        </div>
      </div>

      {/* Steps */}
      <div>
        <label style={labelStyle}>Inference Steps &mdash; {params.steps}</label>
        <input
          type="range" min={10} max={100} step={5}
          value={params.steps}
          onChange={e => setParams(p => ({ ...p, steps: parseInt(e.target.value) }))}
          style={{ width: '100%', accentColor: '#6c63ff' }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#404040' }}>
          <span>10</span><span>100</span>
        </div>
      </div>

      {/* Seed */}
      <div>
        <label style={labelStyle}>Seed (-1 = random)</label>
        <input
          type="number"
          value={params.seed}
          onChange={e => setParams(p => ({ ...p, seed: parseInt(e.target.value) || -1 }))}
          style={inputStyle}
        />
      </div>

      {/* Motion Bucket ID - only relevant for video */}
      {params.mode === 'video' && (
        <div>
          <label style={labelStyle}>Motion Bucket ID &mdash; {params.motion_bucket_id}</label>
          <input
            type="range" min={1} max={255} step={1}
            value={params.motion_bucket_id}
            onChange={e => setParams(p => ({ ...p, motion_bucket_id: parseInt(e.target.value) }))}
            style={{ width: '100%', accentColor: '#6c63ff' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#404040' }}>
            <span>1 (slow)</span><span>255 (fast)</span>
          </div>
        </div>
      )}

      <div style={{
        marginTop: 'auto', padding: '12px', borderRadius: 10,
        background: 'rgba(108,99,255,0.06)', border: '1px solid rgba(108,99,255,0.12)',
        fontSize: 11, color: '#505050', lineHeight: 1.6,
      }}>
        Tip: Higher CFG = stronger prompt adherence.<br />
        Lower motion bucket = smoother video.<br />
        Set seed for reproducibility.
      </div>
    </motion.aside>
  );
}
