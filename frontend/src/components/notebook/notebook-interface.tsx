'use client'

import React, { useEffect, useState, useCallback } from 'react'
import { useNotebookStore } from '@/lib/stores/notebook-store'
import { JupyterKernelClient, getKernelClient, resetKernelClient } from '@/lib/jupyter/kernel-client'
import { NotebookCell } from './notebook-cell'
import { NotebookToolbar } from './notebook-toolbar'
import { Loader2, AlertCircle } from 'lucide-react'
import { toast } from 'sonner'

interface NotebookInterfaceProps {
  jupyterUrl: string
  jupyterToken?: string
}

export function NotebookInterface({ jupyterUrl, jupyterToken }: NotebookInterfaceProps) {
  const [kernelClient, setKernelClient] = useState<JupyterKernelClient | null>(null)
  const [isInitializing, setIsInitializing] = useState(true)
  const [initError, setInitError] = useState<string | null>(null)

  const {
    cells,
    activeCellId,
    kernelStatus,
    addCell,
    deleteCell,
    updateCellSource,
    updateCellOutputs,
    updateCellStatus,
    updateCellExecutionCount,
    setActiveCellId,
    moveCellUp,
    moveCellDown,
    clearAllOutputs,
    setKernelStatus,
  } = useNotebookStore()

  // Initialize kernel client
  useEffect(() => {
    const initKernel = async () => {
      try {
        setIsInitializing(true)
        setKernelStatus('connecting')

        // Create kernel client
        const client = getKernelClient(jupyterUrl, jupyterToken)
        setKernelClient(client)

        // Start kernel session
        await client.startSession('python3')

        setKernelStatus('idle')
        setIsInitializing(false)
        toast.success('Jupyter kernel connected successfully')
      } catch (error) {
        console.error('Failed to initialize kernel:', error)
        setInitError(error instanceof Error ? error.message : 'Unknown error')
        setKernelStatus('disconnected')
        setIsInitializing(false)
        toast.error('Failed to connect to Jupyter kernel')
      }
    }

    initKernel()

    // Cleanup on unmount
    return () => {
      resetKernelClient()
    }
  }, [jupyterUrl, jupyterToken, setKernelStatus])

  // Execute a single cell
  const executeCell = useCallback(
    async (cellId: string) => {
      if (!kernelClient || !kernelClient.isReady()) {
        toast.error('Kernel is not ready')
        return
      }

      const cell = cells.find((c) => c.id === cellId)
      if (!cell || cell.type !== 'code') return

      try {
        // Set cell status to running
        updateCellStatus(cellId, 'running')
        setKernelStatus('busy')

        // Clear previous outputs
        updateCellOutputs(cellId, [])

        // Execute code
        const result = await kernelClient.executeCode(
          cell.source,
          (output) => {
            // Stream outputs as they arrive
            updateCellOutputs(cellId, [...cells.find((c) => c.id === cellId)?.outputs || [], output])
          },
          (status) => {
            setKernelStatus(status)
          }
        )

        // Update execution count and final outputs
        if (result.executionCount !== null) {
          updateCellExecutionCount(cellId, result.executionCount)
        }
        updateCellOutputs(cellId, result.outputs)

        // Check if there were errors
        const hasError = result.outputs.some((output) => output.output_type === 'error')
        updateCellStatus(cellId, hasError ? 'error' : 'completed')
        setKernelStatus('idle')
      } catch (error) {
        console.error('Cell execution error:', error)
        updateCellStatus(cellId, 'error')
        setKernelStatus('idle')
        toast.error('Cell execution failed')
      }
    },
    [kernelClient, cells, updateCellStatus, updateCellOutputs, updateCellExecutionCount, setKernelStatus]
  )

  // Run all cells sequentially
  const runAllCells = useCallback(async () => {
    for (const cell of cells) {
      if (cell.type === 'code') {
        await executeCell(cell.id)
      }
    }
    toast.success('All cells executed')
  }, [cells, executeCell])

  // Restart kernel
  const restartKernel = useCallback(async () => {
    if (!kernelClient) return

    try {
      setKernelStatus('restarting')
      await kernelClient.restart()
      setKernelStatus('idle')
      clearAllOutputs()
      toast.success('Kernel restarted successfully')
    } catch (error) {
      console.error('Failed to restart kernel:', error)
      toast.error('Failed to restart kernel')
      setKernelStatus('idle')
    }
  }, [kernelClient, setKernelStatus, clearAllOutputs])

  // Interrupt kernel
  const interruptKernel = useCallback(async () => {
    if (!kernelClient) return

    try {
      await kernelClient.interrupt()
      setKernelStatus('idle')
      toast.success('Kernel interrupted')
    } catch (error) {
      console.error('Failed to interrupt kernel:', error)
      toast.error('Failed to interrupt kernel')
    }
  }, [kernelClient, setKernelStatus])

  // Export notebook as JSON
  const exportNotebook = useCallback(() => {
    const notebook = {
      cells: cells.map((cell) => ({
        cell_type: cell.type,
        source: cell.source.split('\n'),
        outputs: cell.outputs,
        execution_count: cell.executionCount,
        metadata: cell.metadata || {},
      })),
      metadata: {
        kernelspec: {
          display_name: 'Python 3',
          language: 'python',
          name: 'python3',
        },
        language_info: {
          name: 'python',
          version: '3.11.0',
        },
      },
      nbformat: 4,
      nbformat_minor: 5,
    }

    const blob = new Blob([JSON.stringify(notebook, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'notebook.ipynb'
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Notebook exported')
  }, [cells])

  // Loading state
  if (isInitializing) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-950">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-snowflake-500 mx-auto mb-4" />
          <p className="text-gray-400">Connecting to Jupyter kernel...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (initError) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-950">
        <div className="text-center max-w-md">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">Failed to Connect</h2>
          <p className="text-gray-400 mb-4">{initError}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-snowflake-600 hover:bg-snowflake-700 rounded text-white transition-colors"
          >
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="notebook-interface h-screen flex flex-col bg-gray-950">
      {/* Toolbar */}
      <NotebookToolbar
        kernelStatus={kernelStatus}
        onAddCodeCell={() => addCell('code', cells.length)}
        onAddMarkdownCell={() => addCell('markdown', cells.length)}
        onRunAll={runAllCells}
        onRestartKernel={restartKernel}
        onInterruptKernel={interruptKernel}
        onClearAllOutputs={clearAllOutputs}
        onExportNotebook={exportNotebook}
      />

      {/* Notebook Content */}
      <div className="flex-1 overflow-auto px-8 py-6">
        <div className="max-w-5xl mx-auto space-y-4">
          {cells.map((cell, index) => (
            <NotebookCell
              key={cell.id}
              cell={cell}
              isActive={cell.id === activeCellId}
              onSourceChange={(source) => updateCellSource(cell.id, source)}
              onRun={() => executeCell(cell.id)}
              onDelete={() => deleteCell(cell.id)}
              onMoveUp={() => moveCellUp(cell.id)}
              onMoveDown={() => moveCellDown(cell.id)}
              onActivate={() => setActiveCellId(cell.id)}
              canMoveUp={index > 0}
              canMoveDown={index < cells.length - 1}
            />
          ))}

          {/* Add cell button at bottom */}
          <div className="flex gap-2 pt-4">
            <button
              onClick={() => addCell('code', cells.length)}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm transition-colors"
            >
              + Code Cell
            </button>
            <button
              onClick={() => addCell('markdown', cells.length)}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm transition-colors"
            >
              + Markdown Cell
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
