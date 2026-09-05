import { useEffect, useRef, useState } from 'react'
import './App.css'

type Message = {
  id: number
  username: string
  trip: string | null
  content: string
  created_at: string
  avatar_url: string | null
}

type Identity = {
  username: string
  trip: string | null
  avatar_url: string | null
}

type ServerEvent = ({ type: 'joined' } & Identity) | (Message & { type: 'message' })

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'
const WS_BASE = import.meta.env.VITE_WS_BASE ?? 'ws://localhost:8000'
const NAME_STORAGE_KEY = 'chatapp:lastName'

function isSameIdentity(a: { username: string; trip: string | null }, b: Identity | null) {
  if (!b) return false
  return a.username === b.username && a.trip === b.trip
}

function resolveAvatarSrc(avatarUrl: string | null) {
  return avatarUrl ? `${API_BASE}${avatarUrl}` : null
}

function Avatar({ username, avatarUrl }: { username: string; avatarUrl: string | null }) {
  const src = resolveAvatarSrc(avatarUrl)
  if (src) {
    return <img className="avatar" src={src} alt={username} />
  }
  return <div className="avatar avatar-fallback">{username.slice(0, 1)}</div>
}

function App() {
  const [nameInput, setNameInput] = useState(
    () => localStorage.getItem(NAME_STORAGE_KEY) ?? '',
  )
  const [joined, setJoined] = useState(false)
  const [identity, setIdentity] = useState<Identity | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [avatarStatus, setAvatarStatus] = useState<'idle' | 'uploading' | 'error'>('idle')
  const wsRef = useRef<WebSocket | null>(null)
  const bottomRef = useRef<HTMLDivElement | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const tripPassword = nameInput.includes('#') ? nameInput.slice(nameInput.indexOf('#') + 1) : ''

  useEffect(() => {
    if (!joined) return

    fetch(`${API_BASE}/messages`)
      .then((res) => res.json())
      .then(setMessages)
      .catch(() => {})

    const ws = new WebSocket(`${WS_BASE}/ws`)
    wsRef.current = ws

    ws.onopen = () => {
      ws.send(JSON.stringify({ name: nameInput }))
    }

    ws.onmessage = (event) => {
      const data: ServerEvent = JSON.parse(event.data)
      if (data.type === 'joined') {
        setIdentity({ username: data.username, trip: data.trip, avatar_url: data.avatar_url })
      } else if (data.type === 'message') {
        setMessages((prev) => [...prev, data])
      }
    }

    return () => {
      ws.close()
    }
  }, [joined, nameInput])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleJoin = (e: React.FormEvent) => {
    e.preventDefault()
    if (!nameInput.trim()) return
    localStorage.setItem(NAME_STORAGE_KEY, nameInput)
    setJoined(true)
  }

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !wsRef.current) return
    wsRef.current.send(JSON.stringify({ content: input }))
    setInput('')
  }

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file || !tripPassword) return

    setAvatarStatus('uploading')
    try {
      const formData = new FormData()
      formData.append('trip_password', tripPassword)
      formData.append('file', file)

      const res = await fetch(`${API_BASE}/avatar`, { method: 'POST', body: formData })
      if (!res.ok) throw new Error('upload failed')
      const data: { trip: string; avatar_url: string | null } = await res.json()

      setIdentity((prev) => (prev ? { ...prev, avatar_url: data.avatar_url } : prev))
      setAvatarStatus('idle')
    } catch {
      setAvatarStatus('error')
      return
    }

    // 過去メッセージにも新アイコンを反映させるための再取得。失敗してもアイコン設定自体は
    // 成功しているので、エラー扱いにはしない(新規メッセージには反映される)
    try {
      const refreshed = await fetch(`${API_BASE}/messages`).then((r) => r.json())
      setMessages(refreshed)
    } catch {
      // 無視して問題ない
    }
  }

  if (!joined) {
    return (
      <div className="join-screen">
        <form onSubmit={handleJoin}>
          <h1>ChatApp</h1>
          <input
            value={nameInput}
            onChange={(e) => setNameInput(e.target.value)}
            placeholder="名前 (例: たろう#合言葉)"
            autoFocus
          />
          <p className="hint">
            「名前#合言葉」の形式で入力すると、同じ合言葉を知っている人だけが再現できるトリップバッジが付きます(任意)。トリップ登録者はアイコン画像も設定できます。
          </p>
          <p className="hint">
            入力内容はこの端末のブラウザに保存され、次回自動で入力されます(共有端末では注意してください)。
          </p>
          <button type="submit">参加する</button>
        </form>
      </div>
    )
  }

  return (
    <div className="chat-screen">
      <header>
        <Avatar username={identity?.username ?? ''} avatarUrl={identity?.avatar_url ?? null} />
        <span>
          ChatApp — {identity?.username ?? '接続中...'}
          {identity?.trip && <span className="trip-badge">◆{identity.trip}</span>}
        </span>
        {identity?.trip && (
          <button
            type="button"
            className="avatar-upload-button"
            onClick={() => fileInputRef.current?.click()}
            disabled={avatarStatus === 'uploading'}
          >
            {avatarStatus === 'uploading' ? '設定中...' : 'アイコン設定'}
          </button>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          hidden
          onChange={handleAvatarChange}
        />
      </header>
      {avatarStatus === 'error' && (
        <p className="avatar-error">アイコンの設定に失敗しました(画像形式・2MB以内かご確認ください)</p>
      )}
      <div className="messages">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`message-row ${isSameIdentity(m, identity) ? 'own' : ''}`}
          >
            <Avatar username={m.username} avatarUrl={m.avatar_url} />
            <div className={`message ${isSameIdentity(m, identity) ? 'own' : ''}`}>
              <span className="meta">
                {m.username}
                {m.trip && <span className="trip-badge">◆{m.trip}</span>}
              </span>
              <span className="content">{m.content}</span>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <form className="composer" onSubmit={handleSend}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="メッセージを入力..."
          autoFocus
        />
        <button type="submit">送信</button>
      </form>
    </div>
  )
}

export default App
