#!/bin/bash

# Nome da imagem que criamos
IMAGE_NAME="ambiente-go-github"

echo "🚀 Iniciando Pipeline Local Docker..."

# 1. Build da imagem (garante que está atualizada)
echo "📦 Passo 1: Atualizando imagem Docker..."
docker build -t $IMAGE_NAME .

# 2. Rodar o Linter (conforme gin.yml)
echo "🔍 Passo 2: Rodando Linter (golangci-lint)..."
docker run --rm $IMAGE_NAME golangci-lint run --verbose

# 3. Rodar os Testes (conforme gin.yml)
echo "🧪 Passo 3: Rodando Testes Unitários..."
docker run --rm $IMAGE_NAME go test -v ./...

# 4. Rodar Scan de Segurança (conforme trivy-scan.yml)
echo "🛡️ Passo 4: Rodando Scan de Segurança (Trivy)..."
docker run --rm $IMAGE_NAME trivy fs .

echo "✅ Todos os passos concluídos com sucesso!"
