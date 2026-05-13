'use client';

import { useEffect, useRef } from 'react';
import { gsap } from 'gsap';

interface IntroAnimationProps {
  onComplete: () => void;
}

export default function IntroAnimation({ onComplete }: IntroAnimationProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const logoRef = useRef<HTMLDivElement>(null);
  const subtitleRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);
  const particlesRef = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const overlay = overlayRef.current;
    const logo = logoRef.current;
    const subtitle = subtitleRef.current;
    if (!overlay || !logo || !subtitle) return;

    const tl = gsap.timeline({
      onComplete: () => {
        gsap.to(overlay, {
          opacity: 0,
          duration: 0.6,
          ease: 'power2.inOut',
          onComplete: () => {
            overlay.style.display = 'none';
            onComplete();
          },
        });
      },
    });

    // Ring animation
    if (ringRef.current) {
      tl.fromTo(ringRef.current,
        { scale: 0.4, opacity: 0 },
        { scale: 1, opacity: 0.25, duration: 1.2, ease: 'power2.out' }, 0);
    }

    // Particles
    particlesRef.current.forEach((p, i) => {
      if (!p) return;
      const angle = (i / 20) * Math.PI * 2;
      const r = 100 + Math.random() * 60;
      tl.to(p, {
        opacity: 0.7, x: Math.cos(angle) * r, y: Math.sin(angle) * r,
        duration: 1, ease: 'power2.out',
      }, 0.1 + i * 0.04);
    });

    tl.fromTo(logo,
      { y: 24, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.7, ease: 'power3.out' }, 0.5);

    tl.fromTo(subtitle,
      { y: 16, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.5, ease: 'power3.out' }, 0.9);

    tl.to({}, { duration: 0.8 });

    return () => { tl.kill(); };
  }, [onComplete]);

  return (
    <div ref={overlayRef} style={{
      position: 'fixed', inset: 0, background: '#050505',
      zIndex: 9999, display: 'flex', alignItems: 'center',
      justifyContent: 'center', overflow: 'hidden',
    }}>
      {/* Particles */}
      {Array.from({ length: 20 }).map((_, i) => (
        <div key={i}
          ref={el => { particlesRef.current[i] = el; }}
          style={{
            position: 'absolute', width: i % 3 === 0 ? 3 : 2, height: i % 3 === 0 ? 3 : 2,
            background: i % 2 === 0 ? '#6c63ff' : '#00d4ff',
            borderRadius: '50%', opacity: 0,
          }}
        />
      ))}

      {/* Ring */}
      <div ref={ringRef} style={{
        position: 'absolute', width: 220, height: 220,
        border: '1px solid rgba(108,99,255,0.3)', borderRadius: '50%', opacity: 0,
      }} />

      {/* Logo */}
      <div style={{ textAlign: 'center', position: 'relative', zIndex: 10 }}>
        <div ref={logoRef} style={{
          fontSize: 44, fontWeight: 800, letterSpacing: '-2px', opacity: 0,
          background: 'linear-gradient(135deg, #6c63ff 0%, #00d4ff 100%)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text',
        }}>
          Identity Gen
        </div>
        <div ref={subtitleRef} style={{
          fontSize: 13, color: '#606060', letterSpacing: '5px',
          textTransform: 'uppercase', marginTop: 10, opacity: 0,
        }}>
          Studio
        </div>
      </div>
    </div>
  );
}
