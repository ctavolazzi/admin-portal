import React, { useEffect, useMemo, useRef, useState } from 'react'
import './styles.css'

function timeAgo(ts) {
  const d = typeof ts === 'number' ? new Date(ts * 1000) : new Date(ts)
  const diff = (Date.now() - d.getTime()) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`
  return `${Math.floor(diff/86400)}d ago`
}
function stripHtml(html = '') {
  try {
    const doc = new DOMParser().parseFromString(html, 'text/html')
    return doc.body.textContent || ''
  } catch { return html.replace(/<[^>]+>/g, '') }
}
function dedupe(items) {
  const seen = new Set()
  const out = []
  for (const it of items) {
    const key = (it.url || it.title || '').toLowerCase()
    if (!key || seen.has(key)) continue
    seen.add(key)
    out.push(it)
  }
  return out
}

const SOURCE_BADGE = {
  'Hacker News': 'badge-blue',
  'GitHub Trending': 'badge-green',
  'Ars Technica': 'badge-blue',
  'Lobsters': 'badge-red'
}

// Sources
async function fetchHackerNewsTop(limit = 20, signal) {
  const ids = await fetch('https://hacker-news.firebaseio.com/v0/topstories.json', { signal }).then(r => r.json())
  const subset = ids.slice(0, limit)
  const items = await Promise.all(subset.map(async id => {
    const item = await fetch(`https://hacker-news.firebaseio.com/v0/item/${id}.json`, { signal }).then(r => r.json())
    return normalizeHN(item)
  }))
  return items
}
function normalizeHN(item) {
  return {
    id: `hn_${item.id}`,
    title: item.title,
    url: item.url || `https://news.ycombinator.com/item?id=${item.id}`,
    source: 'Hacker News',
    published_at: item.time,
    category: 'technology',
    score: item.score || 0,
    comments: item.descendants || 0,
    description: `HN Score: ${item.score || 0}${item.descendants ? ` | Comments: ${item.descendants}` : ''}`
  }
}
async function searchHackerNews(query, page = 0, hitsPerPage = 20, signal) {
  const params = new URLSearchParams({ query, page: String(page), hitsPerPage: String(hitsPerPage), tags: 'story' })
  const url = `https://hn.algolia.com/api/v1/search?${params.toString()}`
  const data = await fetch(url, { signal }).then(r => r.json())
  return (data.hits || []).map(hit => ({
    id: `hn_${hit.objectID}`,
    title: hit.title,
    url: hit.url || `https://news.ycombinator.com/item?id=${hit.objectID}`,
    source: 'Hacker News',
    published_at: hit.created_at,
    category: 'technology',
    score: hit.points || 0,
    comments: hit.num_comments || 0,
    description: `HN Score: ${hit.points || 0}${hit.num_comments ? ` | Comments: ${hit.num_comments}` : ''}`
  }))
}
async function fetchGitHubTrending(limit = 20, signal) {
  const since = new Date(Date.now() - 7*24*3600*1000).toISOString().slice(0,10)
  const url = `https://api.github.com/search/repositories?q=stars:>1+created:>${since}&sort=stars&order=desc&per_page=${limit}`
  const headers = {}
  const token = import.meta?.env?.VITE_GITHUB_TOKEN
  if (token) headers['Authorization'] = `Bearer ${token}`
  const data = await fetch(url, { headers, signal }).then(r => r.json())
  return (data.items || []).map(repo => ({
    id: `gh_${repo.id}`,
    title: `🚀 ${repo.full_name}`,
    url: repo.html_url,
    source: 'GitHub Trending',
    published_at: repo.created_at,
    category: 'programming',
    score: repo.stargazers_count || 0,
    description: repo.description || ''
  }))
}
async function fetchRSS(url, source, limit = 20, signal) {
  const proxy = `https://api.allorigins.win/raw?url=${encodeURIComponent(url)}`
  const xml = await fetch(proxy, { signal }).then(r => r.text())
  const parser = new DOMParser()
  const doc = parser.parseFromString(xml, 'text/xml')
  const items = Array.from(doc.querySelectorAll('item')).slice(0, limit)
  return items.map((it, idx) => ({
    id: `${source}_${idx}_${it.querySelector('guid')?.textContent || it.querySelector('link')?.textContent || idx}`,
    title: stripHtml(it.querySelector('title')?.textContent || 'Untitled'),
    url: it.querySelector('link')?.textContent || '#',
    source,
    published_at: it.querySelector('pubDate')?.textContent || new Date().toISOString(),
    category: 'news',
    score: 0,
    description: stripHtml(it.querySelector('description')?.textContent || '')
  }))
}

const CACHE_KEY = 'newsFeedCacheV5'
const TOPICS_KEY = 'newsTopicsV2'
const UI_KEY = 'newsUiStateV2'

function loadTopics() { try { return JSON.parse(localStorage.getItem(TOPICS_KEY) || '{}') } catch { return {} } }
function saveTopics(topics) { localStorage.setItem(TOPICS_KEY, JSON.stringify(topics)) }
function loadUi() { try { return JSON.parse(localStorage.getItem(UI_KEY) || '{}') } catch { return {} } }
function saveUi(state) { localStorage.setItem(UI_KEY, JSON.stringify(state)) }

function naiveSummary(items) {
  if (!items?.length) return 'No items yet.'
  const sources = new Map()
  let earliest = Infinity, latest = 0
  items.forEach(i => {
    sources.set(i.source, (sources.get(i.source) || 0) + 1)
    const ts = typeof i.published_at === 'number' ? i.published_at*1000 : Date.parse(i.published_at)
    if (!Number.isNaN(ts)) { earliest = Math.min(earliest, ts); latest = Math.max(latest, ts) }
  })
  const srcText = Array.from(sources.entries()).map(([s,c]) => `${c} from ${s}`).join(', ')
  const range = isFinite(earliest) && latest ? `${new Date(earliest).toLocaleDateString()} → ${new Date(latest).toLocaleDateString()}` : 'unknown period'
  return `Collected ${items.length} updates (${srcText}) over ${range}. Recent highlights:\n- ${items.slice(0,3).map(i => i.title).join('\n- ')}`
}

function groupByDay(items = []) {
  const groups = {}
  items.forEach(i => {
    const ts = typeof i.published_at === 'number' ? i.published_at*1000 : Date.parse(i.published_at)
    const d = new Date(ts)
    const key = d.toISOString().slice(0,10)
    ;(groups[key] ||= []).push(i)
  })
  return Object.entries(groups).sort((a,b) => new Date(b[0]) - new Date(a[0]))
}

function idsFrom(items = []) { return items.map(i => i.id) }
function diffIds(prev = [], next = []) {
  const setPrev = new Set(prev)
  const setNext = new Set(next)
  const added = next.filter(id => !setPrev.has(id))
  const removed = prev.filter(id => !setNext.has(id))
  return { added, removed }
}

export default function App() {
  const ui = loadUi()
  const [articles, setArticles] = useState([])
  const [visible, setVisible] = useState(ui.visible ?? 20)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState(ui.filters ?? { hn: true, gh: true, ars: true, lobsters: true, q: '' })
  const [view, setView] = useState(ui.view ?? 'grid')
  const [backoffUntil, setBackoffUntil] = useState(0)
  const [topics, setTopics] = useState(loadTopics())
  const [activeTopic, setActiveTopic] = useState(ui.activeTopic ?? '')
  const [selected, setSelected] = useState(() => new Set())
  const fileRef = useRef(null)

  useEffect(() => { saveUi({ filters, view, activeTopic, visible }) }, [filters, view, activeTopic, visible])

  const filtered = useMemo(() => {
    let list = articles.filter(a => (
      (filters.hn && a.source === 'Hacker News') ||
      (filters.gh && a.source === 'GitHub Trending') ||
      (filters.ars && a.source === 'Ars Technica') ||
      (filters.lobsters && a.source === 'Lobsters')
    ))
    if (filters.q) {
      const q = filters.q.toLowerCase()
      list = list.filter(a => (a.title||'').toLowerCase().includes(q) || (a.description||'').toLowerCase().includes(q))
    }
    return list
  }, [articles, filters])

  // initial load
  useEffect(() => {
    const cached = localStorage.getItem(CACHE_KEY)
    if (cached) {
      try { const { data, ts } = JSON.parse(cached); if (Date.now() - ts < 2*60*1000) setArticles(data) } catch {}
    }
    let cancelled = false
    const ctrl = new AbortController()
    async function load() {
      if (Date.now() < backoffUntil) return
      setLoading(true); setError(null)
      try {
        const [hnTop, gh, ars, lob] = await Promise.all([
          filters.hn ? fetchHackerNewsTop(40, ctrl.signal) : Promise.resolve([]),
          filters.gh ? fetchGitHubTrending(30, ctrl.signal) : Promise.resolve([]),
          filters.ars ? fetchRSS('https://feeds.arstechnica.com/arstechnica/index', 'Ars Technica', 20, ctrl.signal) : Promise.resolve([]),
          filters.lobsters ? fetchRSS('https://lobste.rs/rss', 'Lobsters', 20, ctrl.signal) : Promise.resolve([])
        ])
        const merged = dedupe([...hnTop, ...gh, ...ars, ...lob])
        merged.sort((a, b) => {
          const ta = typeof a.published_at === 'number' ? a.published_at : Date.parse(a.published_at)/1000
          const tb = typeof b.published_at === 'number' ? b.published_at : Date.parse(b.published_at)/1000
          return (tb||0) - (ta||0)
        })
        if (!cancelled) { setArticles(merged); localStorage.setItem(CACHE_KEY, JSON.stringify({ data: merged, ts: Date.now() })) }
      } catch (e) {
        if (e?.name === 'AbortError') return
        if (!cancelled) { setError(e.message || 'Failed to load'); setBackoffUntil(Date.now() + 60*1000) }
      } finally { if (!cancelled) setLoading(false) }
    }
    load(); const t = setInterval(load, 5*60*1000)
    return () => { cancelled = true; ctrl.abort(); clearInterval(t) }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.hn, filters.gh, filters.ars, filters.lobsters])

  async function runSearch(query) {
    setLoading(true); setError(null)
    try {
      const ctrl = new AbortController()
      const [hn] = await Promise.all([
        searchHackerNews(query, 0, 50, ctrl.signal)
      ])
      const merged = dedupe([...hn])
      merged.sort((a, b) => {
        const ta = typeof a.published_at === 'number' ? a.published_at : Date.parse(a.published_at)/1000
        const tb = typeof b.published_at === 'number' ? b.published_at : Date.parse(b.published_at)/1000
        return (tb||0) - (ta||0)
      })
      setArticles(merged); setVisible(20)
    } catch (e) { setError(e.message || 'Search failed') } finally { setLoading(false) }
  }

  function onSearchChange(e) { setFilters(prev => ({ ...prev, q: e.target.value })) }
  function onSearchSubmit(e) { e.preventDefault(); if (filters.q.trim()) runSearch(filters.q.trim()) }

  function addTopicFromQuery() {
    const q = filters.q.trim(); if (!q) return
    const key = q.toLowerCase(); if (topics[key]) return setActiveTopic(key)
    const next = { ...topics, [key]: { query: q, items: [], created_at: Date.now(), last_checked: 0, new_count: 0, last_snapshot: [] } }
    setTopics(next); saveTopics(next); setActiveTopic(key)
  }
  function saveItemToTopic(item) {
    if (!activeTopic) return
    const t = topics[activeTopic]; if (!t) return
    if (t.items.find(i => i.id === item.id)) return
    const updated = { ...topics, [activeTopic]: { ...t, items: [item, ...t.items] } }
    setTopics(updated); saveTopics(updated)
  }
  function removeTopic(key) { const next = { ...topics }; delete next[key]; setTopics(next); saveTopics(next); if (activeTopic === key) setActiveTopic('') }

  async function copyLink(url) { try { await navigator.clipboard.writeText(url) } catch {} }

  // Multi-select helpers
  function toggleSelect(id) { setSelected(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n }) }
  function clearSelection() { setSelected(new Set()) }
  function selectVisible() { setSelected(new Set(filtered.slice(0, visible).map(a => a.id))) }
  function saveSelectedToTopic() {
    if (!activeTopic) return
    const t = topics[activeTopic]; if (!t) return
    const toSave = filtered.slice(0, visible).filter(a => selected.has(a.id))
    const existing = new Set(t.items.map(i => i.id))
    const merged = [...toSave.filter(a => !existing.has(a.id)), ...t.items]
    const updated = { ...topics, [activeTopic]: { ...t, items: merged } }
    setTopics(updated); saveTopics(updated); clearSelection()
  }
  async function copySelectedLinks() { const links = filtered.slice(0, visible).filter(a => selected.has(a.id)).map(a => a.url).join('\n'); if (links) await copyLink(links) }
  function saveAllVisibleToTopic() { setSelected(new Set(filtered.slice(0, visible).map(a => a.id))); saveSelectedToTopic() }

  // Topic intelligence
  async function refreshTopic(key) {
    const t = topics[key]; if (!t) return
    try {
      const hits = await searchHackerNews(t.query, 0, 50)
      const nextIds = idsFrom(hits)
      const { added, removed } = diffIds(t.last_snapshot || [], nextIds)
      const updated = {
        ...topics,
        [key]: {
          ...t,
          last_checked: Date.now(),
          new_count: added.length,
          last_snapshot: nextIds,
          last_diff: { added, removed },
          last_hits: hits
        }
      }
      setTopics(updated); saveTopics(updated)
    } catch (e) { /* ignore per-topic errors */ }
  }
  async function refreshAllTopics() { await Promise.all(Object.keys(topics).map(refreshTopic)) }
  function markTopicSeen(key) {
    const t = topics[key]; if (!t) return
    const updated = { ...topics, [key]: { ...t, new_count: 0 } }
    setTopics(updated); saveTopics(updated)
  }
  function changeSummary(t) {
    if (!t?.last_diff) return 'No recent checks.'
    const { added = [], removed = [] } = t.last_diff
    const a = added.length ? `${added.length} new` : 'no new'
    const r = removed.length ? `${removed.length} gone` : 'none removed'
    return `Since last check: ${a}, ${r}.`
  }

  // Export / Import
  function exportTopics() {
    const blob = new Blob([JSON.stringify(topics, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'topics.json'; a.click(); URL.revokeObjectURL(url)
  }
  function onImportFile(e) {
    const file = e.target.files?.[0]; if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      try { const data = JSON.parse(String(reader.result)); setTopics(data); saveTopics(data) } catch {}
    }
    reader.readAsText(file)
  }

  // Keyboard shortcuts
  useEffect(() => {
    function onKey(e) {
      if (e.key === '/') { e.preventDefault(); const el = document.querySelector('input.search'); el?.focus() }
      if (e.key === 'Escape') clearSelection()
      if (e.key.toLowerCase() === 'a' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); selectVisible() }
      if (e.key.toLowerCase() === 's' && activeTopic) { e.preventDefault(); saveSelectedToTopic() }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [activeTopic, filtered, visible, selected])

  const topicList = Object.entries(topics).sort((a,b) => b[1].created_at - a[1].created_at)
  const activeDossier = activeTopic ? topics[activeTopic] : null

  return (
    <div className="container">
      <div className="header">
        <div className="brand">
          <div className="brand-badge" />
          <div>
            <h1 className="title">News Dashboard</h1>
            <p className="subtitle">Free APIs: HN, GitHub, Ars Technica, Lobsters</p>
          </div>
        </div>
        <div className="row">
          <button className="action" aria-label="Check all topics" onClick={refreshAllTopics}>Check updates</button>
          <select className="select" aria-label="View" value={view} onChange={e => setView(e.target.value)}>
            <option value="grid">Grid</option>
            <option value="list">List</option>
          </select>
          <div className="badges">
            <span className="badge badge-blue">v1</span>
            {backoffUntil > Date.now() && <span className="badge badge-red">Rate limited</span>}
          </div>
        </div>
      </div>

      <div className="controls">
        <label className="chip"><input type="checkbox" checked={filters.hn} onChange={e => setFilters(p => ({...p, hn: e.target.checked}))}/> HN</label>
        <label className="chip"><input type="checkbox" checked={filters.gh} onChange={e => setFilters(p => ({...p, gh: e.target.checked}))}/> GitHub</label>
        <label className="chip"><input type="checkbox" checked={filters.ars} onChange={e => setFilters(p => ({...p, ars: e.target.checked}))}/> Ars</label>
        <label className="chip"><input type="checkbox" checked={filters.lobsters} onChange={e => setFilters(p => ({...p, lobsters: e.target.checked}))}/> Lobsters</label>
        <form onSubmit={onSearchSubmit} style={{ display: 'flex', gap: 10, flex: 1 }}>
          <input className="search" placeholder="Search topics (e.g., OpenAI, TypeScript)" value={filters.q} onChange={onSearchChange} aria-label="Search" />
          <button className="button" type="submit">Search</button>
          <button type="button" className="button" onClick={addTopicFromQuery}>Track topic</button>
        </form>
      </div>

      <div className="layout">
        <aside className="card" style={{ padding: 12 }}>
          <div className="meta" style={{ marginBottom: 10 }}>
            <strong>Tracked Topics</strong>
            <span className="badge badge-green">{topicList.length}</span>
          </div>
          <div className="row" style={{ marginBottom: 8 }}>
            <button className="action" onClick={exportTopics}>Export</button>
            <button className="action" onClick={() => fileRef.current?.click()}>Import</button>
            <input ref={fileRef} type="file" accept="application/json" onChange={onImportFile} style={{ display: 'none' }} />
          </div>
          {topicList.length === 0 && <p style={{ color: 'var(--muted)' }}>Create a topic from a search.</p>}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {topicList.map(([key, t]) => (
              <div key={key} className="card" style={{ padding: 10, cursor: 'pointer', borderColor: activeTopic === key ? 'rgba(255,255,255,0.25)' : undefined }} onClick={() => { setActiveTopic(key); markTopicSeen(key) }}>
                <div className="meta">
                  <span>{t.query}</span>
                  <span className="row" style={{ gap: 6 }}>
                    {t.new_count > 0 && <span className="badge badge-red">{t.new_count} new</span>}
                    <span className="badge badge-blue">{t.items.length}</span>
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--muted)' }}>checked {t.last_checked ? timeAgo(t.last_checked) : 'never'}</div>
                {t.last_diff && <div style={{ fontSize: 12, color: 'var(--muted)' }}>{changeSummary(t)}</div>}
                <div style={{ marginTop: 6, display: 'flex', gap: 6 }}>
                  <button className="button ghost" onClick={(e) => { e.stopPropagation(); refreshTopic(key) }}>Check</button>
                  <button className="button ghost" onClick={(e) => { e.stopPropagation(); removeTopic(key) }}>Remove</button>
                </div>
              </div>
            ))}
          </div>
        </aside>

        <main>
          {loading && (<div>{Array.from({ length: 8 }).map((_, i) => (<div key={i} className="skeleton" />))}</div>)}
          {error && (<div className="toast">Error: {error}</div>)}

          {/* Dossier view */}
          {activeDossier && (
            <div className="card" style={{ marginBottom: 16 }}>
              <div className="meta"><strong>Dossier</strong><span>{activeDossier.query}</span></div>
              <p style={{ whiteSpace: 'pre-line' }}>{naiveSummary(activeDossier.items)}</p>
              {activeDossier.items.length > 0 && (
                groupByDay(activeDossier.items).map(([day, items]) => (
                  <div key={day} className="card" style={{ marginTop: 10 }}>
                    <div className="meta"><strong>{new Date(day).toLocaleDateString()}</strong><span className="badge badge-blue">{items.length}</span></div>
                    <div className={`grid ${view === 'grid' ? 'dense' : ''}`}>
                      {items.map(it => (
                        <div key={it.id} className="card">
                          <div className="meta"><span className={`badge ${SOURCE_BADGE[it.source] || 'badge-blue'}`}>{it.source}</span><span>{timeAgo(it.published_at)}</span></div>
                          <a href={it.url} target="_blank" rel="noreferrer"><h3>{it.title}</h3></a>
                          {it.description && <p>{it.description}</p>}
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Feed */}
          {!loading && (
            <>
              <div className="row" style={{ margin: '8px 0' }}>
                <button className="action" onClick={selectVisible}>Select visible</button>
                <button className="action" onClick={clearSelection}>Clear selection</button>
                {activeTopic && <>
                  <button className="action" onClick={saveSelectedToTopic}>Save selected to "{topics[activeTopic]?.query}"</button>
                  <button className="action" onClick={saveAllVisibleToTopic}>Save all visible</button>
                </>}
                <button className="action" onClick={copySelectedLinks}>Copy selected links</button>
                <span className="badge badge-blue">{selected.size} selected</span>
              </div>
              <div className={`grid ${view === 'grid' ? 'dense' : ''}`}>
                {filtered.slice(0, visible).map(a => (
                  <div key={a.id} className="card" onClick={(e) => { if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'A') toggleSelect(a.id) }} style={{ outline: selected.has(a.id) ? '2px solid rgba(100,200,255,0.6)' : 'none' }}>
                    <div className="meta">
                      <span className={`badge ${SOURCE_BADGE[a.source] || 'badge-blue'}`} style={{ alignSelf: 'flex-start' }}>{a.source}</span>
                      <div className="badges">
                        {a.score ? <span className="badge badge-green">★ {a.score}</span> : null}
                        {typeof a.comments === 'number' && a.comments > 0 ? <span className="badge badge-blue">💬 {a.comments}</span> : null}
                        <span>{timeAgo(a.published_at)}</span>
                      </div>
                    </div>
                    <a href={a.url} target="_blank" rel="noreferrer"><h3>{a.title}</h3></a>
                    {a.description && <p>{a.description}</p>}
                    <div className="actions">
                      <button className="action" onClick={() => window.open(a.url, '_blank')}>Open</button>
                      <button className="action" onClick={() => copyLink(a.url)}>Copy link</button>
                      {activeTopic && <button className="action" onClick={() => saveItemToTopic(a)}>Save to "{topics[activeTopic]?.query}"</button>}
                      <button className="action" onClick={() => toggleSelect(a.id)}>{selected.has(a.id) ? 'Unselect' : 'Select'}</button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {!loading && filtered.length > visible && (
            <div style={{ marginTop: 16 }}>
              <button className="button" onClick={() => setVisible(v => v + 20)}>Load more</button>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
