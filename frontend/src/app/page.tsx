'use client'

import { DeploymentConfig } from '@/components/deployment/deployment-config'
import { DeploymentStatus } from '@/components/deployment/deployment-status'
import { NotebookInterface } from '@/components/notebook/notebook-interface'
import { Header } from '@/components/layout/header'
import { useDeploymentStore } from '@/lib/stores/deployment-store'

export default function HomePage() {
  const { deploymentStatus, notebookUrl } = useDeploymentStore()

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="mb-12 text-center">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-snowflake-400 to-snowflake-600 bg-clip-text text-transparent">
            Housing Crisis Prediction Ensemble
          </h1>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Deploy GPU-accelerated ML infrastructure with custom Jupyter notebooks in minutes
          </p>
        </div>

        {/* Main Content */}
        {!notebookUrl ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Deployment Configuration */}
            <div className="lg:col-span-1">
              <DeploymentConfig />
            </div>

            {/* Deployment Status */}
            <div className="lg:col-span-1">
              {deploymentStatus && <DeploymentStatus />}
            </div>
          </div>
        ) : (
          /* Notebook Interface */
          <NotebookInterface />
        )}
      </main>
    </div>
  )
}
