import { useState } from 'react'
const media = import.meta.env.BASE_URL + 'media/'
export const DEFAULT_IMAGE = media + 'default-star.jpg'
export const DEFAULT_VIDEO = media + 'default-star.mp4'
export function StarImage({ src, title, className = '' }: { src: string | null; title: string; className?: string }) {
 const [failed, setFailed] = useState(false)
 return <img className={className} src={failed ? DEFAULT_IMAGE : src || DEFAULT_IMAGE} alt={title} onError={() => setFailed(true)} />
}
export function StarVideo({ src, poster, controls = false }: { src: string | null; poster: string | null; controls?: boolean }) {
 const requested = src || DEFAULT_VIDEO
 const [failedSource, setFailedSource] = useState<string | null>(null)
 const target = failedSource === requested ? DEFAULT_VIDEO : requested
 const [visibleSource, setVisibleSource] = useState<string | null>(null)

 const sources = Array.from(new Set([visibleSource, target].filter((url): url is string => url !== null)))
 return <div className="video-stack">
  {sources.map(url => <video key={url} className="star-video" src={url}
   poster={visibleSource === null ? poster || DEFAULT_IMAGE : undefined}
   style={{ visibility: visibleSource === null || url === visibleSource ? 'visible' : 'hidden' }}
   autoPlay muted loop playsInline preload="auto" controls={controls}
   onPlaying={() => { if (url === target) setVisibleSource(url) }}
   onError={() => { if (url === target && url !== DEFAULT_VIDEO) setFailedSource(requested) }} />)}
 </div>
}
