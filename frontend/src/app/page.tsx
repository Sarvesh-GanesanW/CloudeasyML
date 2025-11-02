'use client'

import { DeploymentConfig } from '@/components/deployment/deployment-config'
import { DeploymentStatus } from '@/components/deployment/deployment-status'
import { NotebookInterface } from '@/components/notebook/notebook-interface'
import { useDeploymentStore } from '@/lib/stores/deployment-store'

export default function HomePage() {
  const notebookUrl = useDeploymentStore((state) => state.notebookUrl)
  const jupyterToken = useDeploymentStore((state) => state.jupyterToken)
  const deploymentStatus = useDeploymentStore((state) => state.deploymentStatus)

  // If notebook is ready, show it fullscreen
  if (notebookUrl) {
    return <NotebookInterface jupyterUrl={notebookUrl} jupyterToken={jupyterToken} />
  }

  // If deployment is in progress, show status
  if (deploymentStatus && deploymentStatus.phase !== 'idle') {
    return (
      <div className="min-h-screen p-8">
        <div className="max-w-4xl mx-auto">
          <DeploymentStatus />
        </div>
      </div>
    )
  }

  // Default: Show deployment configuration
  return (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">
            HCPE Deployment
          </h1>
          <p className="text-muted-foreground">
            Configure and deploy your GPU-accelerated ML infrastructure
          </p>
        </div>
        <DeploymentConfig />
      </div>
    </div>
  )
}
