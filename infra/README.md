# Infrastructure — Azure Bicep Templates

This directory contains all Azure infrastructure-as-code for the Finance AI Agent platform.

## Architecture

```
Resource Group
├── Application Insights + Log Analytics Workspace
├── Storage Account (Function App + Finance Documents)
├── Key Vault (Secrets with RBAC)
├── PostgreSQL Flexible Server + financedb database
└── Function App (Python 3.11, Consumption Plan, Managed Identity)
```

## Prerequisites

- Azure CLI: `az --version`
- Azure Functions Core Tools: `func --version`
- An Azure subscription and resource group

## Deploy

### 1. Login
```bash
az login
az account set --subscription "<your-subscription-id>"
```

### 2. Create Resource Group
```bash
az group create --name finance-ai-rg --location eastus
```

### 3. Deploy Infrastructure
```bash
cd infra/bicep
az deployment group create \
  --resource-group finance-ai-rg \
  --template-file main.bicep \
  --parameters environmentName=dev dbAdminPassword=<SecurePassword123!>
```

### 4. Deploy Function App Code
```bash
cd backend
func azure functionapp publish <function-app-name>
```

### 5. Set Key Vault Secrets
After deployment, store sensitive values in Key Vault:
```bash
az keyvault secret set --vault-name <kv-name> --name db-password --value "<password>"
az keyvault secret set --vault-name <kv-name> --name azure-openai-api-key --value "<key>"
```

### 6. Grant Managed Identity Access to Key Vault
```bash
az role assignment create \
  --assignee <managed-identity-object-id> \
  --role "Key Vault Secrets User" \
  --scope /subscriptions/<sub>/resourceGroups/finance-ai-rg/providers/Microsoft.KeyVault/vaults/<kv-name>
```

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| environmentName | dev/staging/prod | dev |
| location | Azure region | Resource group location |
| uniqueSuffix | Suffix for unique names | Auto-generated |
| dbAdminUsername | PostgreSQL admin user | pgadmin |
| dbAdminPassword | PostgreSQL admin password | **Required** |
| dbName | Database name | financedb |

## Estimated Costs (Dev)

| Resource | SKU | ~Monthly Cost |
|----------|-----|--------------|
| PostgreSQL | Standard_B1ms | ~$15 |
| Function App | Consumption | ~$0 (pay per use) |
| Storage | Standard LRS | ~$1 |
| App Insights | Per GB | ~$3 |
| Key Vault | Standard | ~$1 |
