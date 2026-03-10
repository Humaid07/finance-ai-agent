// functionapp.bicep - Azure Functions App (Python, consumption plan)

@description('Function App name')
param functionAppName string

@description('App Service Plan name')
param appServicePlanName string

@description('Azure region')
param location string

@description('Storage account name for Function App')
param storageAccountName string

@description('Application Insights connection string')
param appInsightsConnectionString string

@description('Environment name')
param environmentName string

@description('PostgreSQL host')
param dbHost string

@description('Database name')
param dbName string

@description('Database admin user')
param dbUser string

@description('Key Vault name (for secret references)')
param keyVaultName string

// Reference existing storage account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

// Consumption plan (serverless)
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  tags: {
    environment: environmentName
    project: 'finance-ai-agent'
  }
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  kind: 'functionapp'
  properties: {
    reserved: true  // Required for Linux
  }
}

// Function App with system-assigned Managed Identity
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  tags: {
    environment: environmentName
    project: 'finance-ai-agent'
  }
  identity: {
    type: 'SystemAssigned'  // Managed Identity for Key Vault access
  }
  properties: {
    serverFarmId: appServicePlan.id
    reserved: true
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      pythonVersion: '3.11'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsightsConnectionString
        }
        {
          name: 'DB_HOST'
          value: dbHost
        }
        {
          name: 'DB_PORT'
          value: '5432'
        }
        {
          name: 'DB_NAME'
          value: dbName
        }
        {
          name: 'DB_USER'
          value: dbUser
        }
        {
          name: 'DB_SSLMODE'
          value: 'require'
        }
        {
          name: 'ENVIRONMENT'
          value: environmentName
        }
        // Secrets are referenced from Key Vault via managed identity
        // Set these manually or via a separate deployment step:
        // DB_PASSWORD -> @Microsoft.KeyVault(VaultName=<kv>;SecretName=db-password)
        // AZURE_OPENAI_API_KEY -> @Microsoft.KeyVault(...)
      ]
      cors: {
        allowedOrigins: ['*']
        supportCredentials: false
      }
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
    }
    httpsOnly: true
  }
}

output functionAppId string = functionApp.id
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output managedIdentityPrincipalId string = functionApp.identity.principalId
