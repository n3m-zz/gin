# 1. Base: Usando a imagem oficial do Go (Debian) para ter compatibilidade
FROM golang:1.24-bullseye

# 2. Configurações de ambiente (extraídas do gin.yml)
ENV GO111MODULE=on
ENV GOPROXY=https://proxy.golang.org
ENV DEBIAN_FRONTEND=noninteractive

# 3. Instala dependências básicas de sistema (necessárias para o runner e ferramentas)
RUN apt-get update && apt-get install -y \
    curl \
    git \
    sudo \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Instala o golangci-lint (conforme exigido no gin.yml)
RUN curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $(go env GOPATH)/bin v1.54.2

# 5. Instala o Trivy (conforme exigido no trivy-scan.yml)
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# 6. Instala o GoReleaser (conforme exigido no goreleaser.yml)
RUN curl -sfL https://install.goreleaser.com/github.com/goreleaser/goreleaser.sh | sh

# 7. Define o diretório de trabalho
WORKDIR /workspace

# 8. Copia os arquivos do seu projeto local para o container
COPY . .

# Comando padrão: inicia um terminal para você rodar os testes ou o linter manualmente
CMD ["/bin/bash"]
