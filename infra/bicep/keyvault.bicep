// keyvault.bicep - Azure Key Vault for secrets management

@description('Key Vault name (3-24 chars, globally unique)')
param name string

@description('Azure region')
param location string

@description('Environment tag')
param environmentName string

@description('Object ID of the principal that will have access (e.g., the Function App managed identity)')
param accessPolicyObjectId string = ''

resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: name
  location: location
  tags: {
    environment: environmentName
    project: 'finance-ai-agent'
  }
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true   // Use RBAC instead of legacy access policies
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enabledForDeployment: false
    enabledForTemplateDeployment: true
    enabledForDiskEncryption: false
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

output keyVaultId string = keyVault.id
output keyVaultUri string = keyVault.properties.vaultUri
output keyVaultName string = keyVault.name
