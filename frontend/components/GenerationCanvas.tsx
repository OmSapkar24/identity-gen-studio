'use client';
import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import ControlSidebar from './ControlSidebar';

interface JobParams {
  prompt: string;
  mode: 'image' | 'video';
  cfg_scale: number;
  seed: number;
  motion_bucket_id: number;
  steps: number;
}

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function GenerationCanvas() {
  const [faceFile, setFaceFile] = useState<File | null>(null);
  const [facePreview, setFacePreview] = useState<string | null>(null);
  const [params, setParams] = useState<JobParams>({
    prompt: '',
    mode: 'image',
    cfg_scale: 7.5,
    seed: -1,
    motion_bucket_id: 127,
    steps: 30,
  });
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string>('');
  const [progress, setProgress] = useState(0);
  const [outputUrl, setOutputUrl] = useState<string | null>(null);
  const [cometUrl, setCometUrl] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const onDrop = useCallback((files: File[]) => {
    if (!files.length) return;
    const f = files[0];
    setFaceFile(f);
    setFacePreview(URL.createObjectURL(f));
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': [] },
    maxFiles: 1,
  });

  const pollJob = async (jobId: string) => {
    while (true) {
      await new Promise(r => setTimeout(r, 1500));
      const res = await fetch(`${API}/jobs/${jobId}`);
      const data = await res.json();
      setStatus(data.status);
      if (data.progress !== undefined) setProgress(data.progress);
      if (data.status === 'completed') {
        setOutputUrl(data.output_url);
        setCometUrl(data.comet_url || null);
        setBusy(false);
        return;
      }
      if (data.status === 'failed') {
        setStatus('failed');
        setBusy(false);
        return;
      }
    }
  };

  const generate = async () => {
    if (!faceFile || !params.prompt.trim()) return;
    setBusy(true);
    setOutputUrl(null);
    setCometUrl(null);
    setStatus('queued');
    setProgress(0);

    const form = new FormData();
    form.append('face_image', faceFile);
    form.append('prompt', params.prompt);
    form.append('mode', params.mode);
    form.append('cfg_scale', String(params.cfg_scale));
    form.append('seed', String(params.seed));
    form.append('motion_bucket_id', String(params.motion_bucket_id));
    form.append('steps', String(params.steps));

    const res = await fetch(`${API}/generate`, { method: 'POST', body: form });
    const data = await res.json();
    if (data.job_id) await pollJob(data.job_id);
    else { setStatus('failed'); setBusy(false); }
  };

  return (
    <div style={{ display:'flex', minHeight:'100vh', background:'#050505', color:'white', fontFamily:'Inter,sans-serif' }}>
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            key="sidebar"
            initial={{ x: -320, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -320, opacity: 0 }}
            transition={{ type:'spring', stiffness:260, damping:28 }}
            style={{ width:300, flexShrink:0 }}
          >
            <ControlSidebar params={params} setParams={setParams} onClose={() => setSidebarOpen(false)} />
          </motion.div>
        )}
      </AnimatePresence>

      <div style={{ flex:1, display:'flex', flexDirection:'column', alignItems:'center', padding:'40px 24px' }}>
        {!sidebarOpen && (
          <motion.button
            whileHover={{ scale:1.05 }}
            onClick={() => setSidebarOpen(true)}
            style={{ alignSelf:'flex-start', marginBottom:16, padding:'6px 14px', borderRadius:8,
              background:'rgba(108,99,255,0.15)', border:'1px solid rgba(108,99,255,0.3)',
              color:'#a89dff', cursor:'pointer', fontSize:13 }}
          >
            &#9776; Settings
          </motion.button>
        )}

        <motion.h1
          initial={{ opacity:0, y:-20 }}
          animate={{ opacity:1, y:0 }}
          style={{ fontSize:28, fontWeight:700, marginBottom:8,
            background:'linear-gradient(135deg,#6c63ff,#8b5cf6)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent' }}
        >
          Identity Generation Studio
        </motion.h1>
        <p style={{ color:'#606060', marginBottom:32, fontSize:14 }}>Upload a face &rarr; describe the scene &rarr; generate</p>

        {/* Drop zone */}
        <div {...getRootProps()} style={{
          width:'100%', maxWidth:480, height:160, borderRadius:16,
          border:`2px dashed ${isDragActive ? '#6c63ff' : '#2a2a2a'}`,
          display:'flex', alignItems:'center', justifyContent:'center',
          cursor:'pointer', marginBottom:24, position:'relative', overflow:'hidden',
          background:'rgba(108,99,255,0.04)',
        }}>
          <input {...getInputProps()} />
          {facePreview ? (
            <img src={facePreview} alt="face" style={{ height:'100%', objectFit:'cover', borderRadius:14 }} />
          ) : (
            <p style={{ color:'#404040', fontSize:14 }}>{isDragActive ? 'Drop it!' : 'Drag & drop a face image, or click'}</p>
          )}
        </div>

        {/* Prompt */}
        <textarea
          placeholder="Describe the scene (e.g. cyberpunk cityscape, golden hour, 4K)"
          value={params.prompt}
          onChange={e => setParams(p => ({ ...p, prompt: e.target.value }))}
          rows={3}
          style={{
            width:'100%', maxWidth:480, padding:'12px 16px', borderRadius:12,
            background:'rgba(255,255,255,0.04)', border:'1px solid #2a2a2a',
            color:'white', fontSize:14, resize:'vertical', marginBottom:16,
            outline:'none', fontFamily:'inherit',
          }}
        />

        {/* Mode toggle */}
        <div style={{ display:'flex', gap:8, marginBottom:24 }}>
          {(['image','video'] as const).map(m => (
            <motion.button
              key={m}
              whileHover={{ scale:1.04 }}
              whileTap={{ scale:0.97 }}
              onClick={() => setParams(p => ({ ...p, mode: m }))}
              style={{
                padding:'8px 20px', borderRadius:20, fontSize:13, cursor:'pointer',
                fontWeight: params.mode === m ? 700 : 400,
                background: params.mode === m ? 'linear-gradient(135deg,#6c63ff,#8b5cf6)' : 'rgba(255,255,255,0.04)',
                border: params.mode === m ? 'none' : '1px solid #2a2a2a',
                color: params.mode === m ? 'white' : '#606060',
              }}
            >
              {m === 'image' ? '🖼 Image' : '🎬 Video'}
            </motion.button>
          ))}
        </div>

        {/* Generate btn */}
        <motion.button whileHover={{scale:1.02}} whileTap={{scale:0.98}} onClick={generate} disabled={busy}
          style={{
            padding:'14px 24px', borderRadius:12, border:'none', fontSize:15, fontWeight:700, cursor:busy?'not-allowed':'pointer',
            background: busy?'#1a1a1a':'linear-gradient(135deg,#6c63ff,#8b5cf6)',
            color: busy?'#606060':'white',
            boxShadow: busy?'none':'0 4px 20px rgba(108,99,255,0.4)',
          }}
        >
          {status===''?'Generate':status==='queued'?'Queued...':status==='processing'?`Generating ${progress}%...`:status==='uploading'?'Uploading...':'Generate'}
        </motion.button>

        {cometUrl && (
          <motion.a initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} href={cometUrl} target="_blank" rel="noopener noreferrer"
            style={{padding:'10px 16px',background:'rgba(108,99,255,0.08)',border:'1px solid rgba(108,99,255,0.2)',
            borderRadius:8,color:'#6c63ff',fontSize:13,textDecoration:'none',fontWeight:500,display:'block',marginTop:16}}>
            View Experiment in Comet ML
          </motion.a>
        )}

        {/* Output */}
        <AnimatePresence>
          {outputUrl && (
            <motion.div
              initial={{ opacity:0, scale:0.96 }}
              animate={{ opacity:1, scale:1 }}
              exit={{ opacity:0 }}
              style={{ marginTop:32, borderRadius:16, overflow:'hidden',
                border:'1px solid rgba(108,99,255,0.2)', maxWidth:480, width:'100%' }}
            >
              {params.mode === 'image' ? (
                <img src={outputUrl} alt="output" style={{ width:'100%', display:'block' }} />
              ) : (
                <video src={outputUrl} controls autoPlay loop style={{ width:'100%', display:'block' }} />
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {status === 'failed' && (
          <p style={{ color:'#ff4444', marginTop:16, fontSize:13 }}>Generation failed. Please try again.</p>
        )}
      </div>
    </div>
  );
}
