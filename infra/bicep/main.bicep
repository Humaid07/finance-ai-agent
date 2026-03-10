// main.bicep - Orchestrates all Finance AI Agent Azure resources
// Deploy: az deployment group create --resource-group <rg> --template-file main.bicep --parameters @main.parameters.json

@description('Environment name (dev, staging, prod)')
param environmentName string = 'dev'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Unique suffix for globally unique resource names')
param uniqueSuffix string = uniqueString(resourceGroup().id)

@description('PostgreSQL admin username')
param dbAdminUsername string = 'pgadmin'

@secure()
@description('PostgreSQL admin password')
param dbAdminPassword string

@description('Database name')
param dbName string = 'financedb'

// Resource naming
var prefix = 'finance-${environmentName}'
var storageAccountName = 'fin${environmentName}${uniqueSuffix}'
var functionAppName = '${prefix}-func-${uniqueSuffix}'
var appServicePlanName = '${prefix}-asp'
var appInsightsName = '${prefix}-insights'
var keyVaultName = 'fin-kv-${uniqueSuffix}'
var postgresServerName = '${prefix}-pg-${uniqueSuffix}'

// ── Application Insights ──────────────────────────────────────────────────
module appInsights 'appinsights.bicep' = {
  name: 'appInsightsDeploy'
  params: {
    name: appInsightsName
    location: location
    environmentName: environmentName
  }
}

// ── Storage Account ───────────────────────────────────────────────────────
module storage 'storage.bicep' = {
  name: 'storageDeploy'
  params: {
    name: storageAccountName
    location: location
    environmentName: environmentName
  }
}

// ── Key Vault ─────────────────────────────────────────────────────────────
module keyVault 'keyvault.bicep' = {
  name: 'keyVaultDeploy'
  params: {
    name: keyVaultName
    location: location
    environmentName: environmentName
  }
}

// ── PostgreSQL Flexible Server ────────────────────────────────────────────
module postgres 'postgres.bicep' = {
  name: 'postgresDeploy'
  params: {
    serverName: postgresServerName
    location: location
    administratorLogin: dbAdminUsername
    administratorPassword: dbAdminPassword
    databaseName: dbName
    environmentName: environmentName
  }
}

// ── Function App ──────────────────────────────────────────────────────────
module functionApp 'functionapp.bicep' = {
  name: 'functionAppDeploy'
  params: {
    functionAppName: functionAppName
    appServicePlanName: appServicePlanName
    location: location
    storageAccountName: storageAccountName
    appInsightsConnectionString: appInsights.outputs.connectionString
    environmentName: environmentName
    dbHost: postgres.outputs.fullyQualifiedDomainName
    dbName: dbName
    dbUser: dbAdminUsername
    keyVaultName: keyVaultName
  }
  dependsOn: [storage, appInsights, postgres, keyVault]
}

// ── Outputs ───────────────────────────────────────────────────────────────
output functionAppUrl string = functionApp.outputs.functionAppUrl
output postgresHost string = postgres.outputs.fullyQualifiedDomainName
output storageAccountName string = storageAccountName
output keyVaultName string = keyVaultName
output appInsightsName string = appInsightsName
