import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

/** Sin HTML en bruto: react-markdown lo descarta por defecto */
export function Markdown({ children }: { children: string }) {
  return (
    <div className="pt-prose">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  )
}
