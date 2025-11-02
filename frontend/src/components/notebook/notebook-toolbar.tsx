'use client'

import React from 'react'
import {
  Play,
  Plus,
  RotateCw,
  Square,
  Trash2,
  Download,
  Upload,
  Save,
  FileCode,
  FileText,
} from 'lucide-react'

interface NotebookToolbarProps {
  kernelStatus: 'disconnected' | 'connecting' | 'connected' | 'busy' | 'idle' | 'restarting'
  onAddCodeCell: () => void
  onAddMarkdownCell: () => void
  onRunAll: () => void
  onRestartKernel: () => void
  onInterruptKernel: () => void
  onClearAllOutputs: () => void
  onSaveNotebook?: () => void
  onLoadNotebook?: () => void
  onExportNotebook?: () => void
}

export function NotebookToolbar({
  kernelStatus,
  onAddCodeCell,
  onAddMarkdownCell,
  onRunAll,
  onRestartKernel,
  onInterruptKernel,
  onClearAllOutputs,
  onSaveNotebook,
  onLoadNotebook,
  onExportNotebook,
}: NotebookToolbarProps) {
  const isKernelBusy = kernelStatus === 'busy' || kernelStatus === 'restarting'
  const isKernelReady = kernelStatus === 'connected' || kernelStatus === 'idle' || kernelStatus === 'busy'

  const getKernelStatusDisplay = () => {
    switch (kernelStatus) {
      case 'disconnected':
        return (
          <span className="flex items-center gap-2 text-red-400">
            <span className="h-2 w-2 rounded-full bg-red-500" />
            Disconnected
          </span>
        )
      case 'connecting':
        return (
          <span className="flex items-center gap-2 text-yellow-400">
            <span className="h-2 w-2 rounded-full bg-yellow-500 animate-pulse" />
            Connecting...
          </span>
        )
      case 'busy':
        return (
          <span className="flex items-center gap-2 text-blue-400">
            <span className="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
            Busy
          </span>
        )
      case 'idle':
      case 'connected':
        return (
          <span className="flex items-center gap-2 text-green-400">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            Ready
          </span>
        )
      case 'restarting':
        return (
          <span className="flex items-center gap-2 text-orange-400">
            <span className="h-2 w-2 rounded-full bg-orange-500 animate-pulse" />
            Restarting...
          </span>
        )
    }
  }

  return (
    <div className="notebook-toolbar flex items-center justify-between px-6 py-3 border-b border-gray-700/50 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-20">
      <div className="flex items-center gap-2">
        {/* Add Cells */}
        <div className="flex items-center gap-1 pr-3 border-r border-gray-700">
          <button
            onClick={onAddCodeCell}
            className="toolbar-btn flex items-center gap-1.5 px-3 py-1.5 rounded bg-gray-800 hover:bg-gray-700 text-sm transition-colors"
            title="Add code cell"
          >
            <Plus className="h-4 w-4" />
            <FileCode className="h-4 w-4" />
            <span>Code</span>
          </button>

          <button
            onClick={onAddMarkdownCell}
            className="toolbar-btn flex items-center gap-1.5 px-3 py-1.5 rounded bg-gray-800 hover:bg-gray-700 text-sm transition-colors"
            title="Add markdown cell"
          >
            <Plus className="h-4 w-4" />
            <FileText className="h-4 w-4" />
            <span>Markdown</span>
          </button>
        </div>

        {/* Run Controls */}
        <div className="flex items-center gap-1 px-3 border-r border-gray-700">
          <button
            onClick={onRunAll}
            disabled={!isKernelReady}
            className="toolbar-btn flex items-center gap-1.5 px-3 py-1.5 rounded bg-green-900/30 hover:bg-green-900/50 text-green-400 text-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            title="Run all cells"
          >
            <Play className="h-4 w-4" />
            <span>Run All</span>
          </button>

          <button
            onClick={onInterruptKernel}
            disabled={!isKernelBusy}
            className="toolbar-btn flex items-center gap-1.5 px-3 py-1.5 rounded bg-orange-900/30 hover:bg-orange-900/50 text-orange-400 text-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            title="Interrupt kernel"
          >
            <Square className="h-4 w-4" />
            <span>Interrupt</span>
          </button>
        </div>

        {/* Kernel Controls */}
        <div className="flex items-center gap-1 px-3 border-r border-gray-700">
          <button
            onClick={onRestartKernel}
            disabled={!isKernelReady}
            className="toolbar-btn flex items-center gap-1.5 px-3 py-1.5 rounded bg-gray-800 hover:bg-gray-700 text-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            title="Restart kernel"
          >
            <RotateCw className="h-4 w-4" />
            <span>Restart</span>
          </button>

          <button
            onClick={onClearAllOutputs}
            className="toolbar-btn flex items-center gap-1.5 px-3 py-1.5 rounded bg-gray-800 hover:bg-gray-700 text-sm transition-colors"
            title="Clear all outputs"
          >
            <Trash2 className="h-4 w-4" />
            <span>Clear Outputs</span>
          </button>
        </div>

        {/* File Operations */}
        {(onSaveNotebook || onLoadNotebook || onExportNotebook) && (
          <div className="flex items-center gap-1 px-3">
            {onSaveNotebook && (
              <button
                onClick={onSaveNotebook}
                className="toolbar-btn p-1.5 rounded bg-gray-800 hover:bg-gray-700 transition-colors"
                title="Save notebook"
              >
                <Save className="h-4 w-4" />
              </button>
            )}

            {onLoadNotebook && (
              <button
                onClick={onLoadNotebook}
                className="toolbar-btn p-1.5 rounded bg-gray-800 hover:bg-gray-700 transition-colors"
                title="Load notebook"
              >
                <Upload className="h-4 w-4" />
              </button>
            )}

            {onExportNotebook && (
              <button
                onClick={onExportNotebook}
                className="toolbar-btn p-1.5 rounded bg-gray-800 hover:bg-gray-700 transition-colors"
                title="Export notebook"
              >
                <Download className="h-4 w-4" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Kernel Status */}
      <div className="flex items-center gap-3">
        <div className="text-xs font-mono">{getKernelStatusDisplay()}</div>
      </div>
    </div>
  )
}
