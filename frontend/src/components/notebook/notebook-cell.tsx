'use client'

import React, { useRef, useEffect, useState } from 'react'
import Editor from '@monaco-editor/react'
import { Play, Trash2, ChevronUp, ChevronDown, Square, Loader2 } from 'lucide-react'
import { NotebookCell as NotebookCellType } from '@/lib/stores/notebook-store'
import { CellOutput } from './cell-output'

interface NotebookCellProps {
  cell: NotebookCellType
  isActive: boolean
  onSourceChange: (source: string) => void
  onRun: () => void
  onDelete: () => void
  onMoveUp: () => void
  onMoveDown: () => void
  onActivate: () => void
  canMoveUp: boolean
  canMoveDown: boolean
}

export function NotebookCell({
  cell,
  isActive,
  onSourceChange,
  onRun,
  onDelete,
  onMoveUp,
  onMoveDown,
  onActivate,
  canMoveUp,
  canMoveDown,
}: NotebookCellProps) {
  const editorRef = useRef<any>(null)
  const [showToolbar, setShowToolbar] = useState(false)

  // Auto-adjust editor height based on content
  const lineCount = cell.source.split('\n').length
  const editorHeight = Math.max(80, Math.min(lineCount * 19 + 40, 500))

  useEffect(() => {
    // Focus editor when cell becomes active
    if (isActive && editorRef.current) {
      editorRef.current.focus()
    }
  }, [isActive])

  const handleEditorMount = (editor: any) => {
    editorRef.current = editor

    // Add keyboard shortcuts
    editor.addCommand(
      monaco.KeyMod.Shift | monaco.KeyCode.Enter,
      () => {
        onRun()
      }
    )

    // Add Ctrl+/ for comment toggle (default, but ensure it's there)
    editor.addCommand(
      monaco.KeyMod.CtrlCmd | monaco.KeyCode.Slash,
      () => {
        editor.trigger('keyboard', 'editor.action.commentLine', {})
      }
    )

    if (isActive) {
      editor.focus()
    }
  }

  const getStatusIcon = () => {
    switch (cell.status) {
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
      case 'completed':
        return null
      case 'error':
        return <Square className="h-4 w-4 text-red-400 fill-current" />
      default:
        return null
    }
  }

  const getStatusColor = () => {
    switch (cell.status) {
      case 'running':
        return 'border-blue-500/50'
      case 'error':
        return 'border-red-500/50'
      default:
        return isActive ? 'border-snowflake-500/50' : 'border-gray-700/30'
    }
  }

  return (
    <div
      className={`notebook-cell group relative rounded-lg border-2 transition-all ${getStatusColor()}`}
      onMouseEnter={() => setShowToolbar(true)}
      onMouseLeave={() => setShowToolbar(false)}
      onClick={onActivate}
    >
      {/* Cell Toolbar */}
      {showToolbar && (
        <div className="absolute -top-3 right-4 flex gap-1 bg-gray-800 rounded-lg border border-gray-700 px-2 py-1 shadow-lg z-10">
          <button
            onClick={(e) => {
              e.stopPropagation()
              onRun()
            }}
            disabled={cell.status === 'running'}
            className="p-1 hover:bg-gray-700 rounded transition-colors disabled:opacity-50"
            title="Run cell (Shift+Enter)"
          >
            <Play className="h-3.5 w-3.5 text-green-400" />
          </button>

          <div className="w-px bg-gray-700 mx-1" />

          <button
            onClick={(e) => {
              e.stopPropagation()
              onMoveUp()
            }}
            disabled={!canMoveUp}
            className="p-1 hover:bg-gray-700 rounded transition-colors disabled:opacity-30"
            title="Move cell up"
          >
            <ChevronUp className="h-3.5 w-3.5" />
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation()
              onMoveDown()
            }}
            disabled={!canMoveDown}
            className="p-1 hover:bg-gray-700 rounded transition-colors disabled:opacity-30"
            title="Move cell down"
          >
            <ChevronDown className="h-3.5 w-3.5" />
          </button>

          <div className="w-px bg-gray-700 mx-1" />

          <button
            onClick={(e) => {
              e.stopPropagation()
              onDelete()
            }}
            className="p-1 hover:bg-red-900/50 rounded transition-colors"
            title="Delete cell"
          >
            <Trash2 className="h-3.5 w-3.5 text-red-400" />
          </button>
        </div>
      )}

      <div className="flex">
        {/* Execution Count / Status */}
        <div className="flex-shrink-0 w-16 flex flex-col items-center justify-start pt-3 border-r border-gray-700/30">
          {cell.type === 'code' && (
            <>
              {getStatusIcon() || (
                <div className="text-xs text-gray-500 font-mono">
                  {cell.executionCount !== null ? `[${cell.executionCount}]` : '[ ]'}
                </div>
              )}
            </>
          )}
        </div>

        {/* Cell Content */}
        <div className="flex-1 min-w-0">
          {cell.type === 'code' ? (
            <>
              {/* Monaco Editor */}
              <div className="editor-container">
                <Editor
                  height={editorHeight}
                  language="python"
                  theme="vs-dark"
                  value={cell.source}
                  onChange={(value) => onSourceChange(value || '')}
                  onMount={handleEditorMount}
                  options={{
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    fontSize: 14,
                    lineNumbers: 'on',
                    glyphMargin: false,
                    folding: true,
                    lineDecorationsWidth: 0,
                    lineNumbersMinChars: 3,
                    renderLineHighlight: 'all',
                    automaticLayout: true,
                    tabSize: 4,
                    wordWrap: 'on',
                    wrappingStrategy: 'advanced',
                    padding: { top: 8, bottom: 8 },
                    scrollbar: {
                      vertical: 'auto',
                      horizontal: 'auto',
                      verticalScrollbarSize: 8,
                      horizontalScrollbarSize: 8,
                    },
                  }}
                />
              </div>

              {/* Cell Outputs */}
              {cell.outputs.length > 0 && (
                <div className="px-4 pb-3">
                  <CellOutput outputs={cell.outputs} />
                </div>
              )}
            </>
          ) : (
            // Markdown cell (simplified for now)
            <div className="p-4">
              <textarea
                value={cell.source}
                onChange={(e) => onSourceChange(e.target.value)}
                className="w-full bg-transparent text-gray-300 resize-none outline-none font-mono text-sm"
                rows={Math.max(3, lineCount)}
                placeholder="Enter markdown..."
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
