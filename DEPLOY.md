# 🚀 Deploy no Dokploy

Guia completo para fazer deploy da app Book Scanner no Dokploy.

## ⚡ Quick Deploy (Recomendado)

### 1️⃣ Push para Git (GitHub, GitLab, etc)

```bash
cd /Users/g/Downloads/parabola

# Inicializar git (se não tiver)
git init
git add .
git commit -m "Initial commit: Book Scanner app"

# Push para seu repositório
git remote add origin https://github.com/seu-usuario/book-scanner.git
git push -u origin main
```

### 2️⃣ No Painel do Dokploy

1. Acesse: https://panel.uatzap.com/dashboard
2. Clique em **"Create Project"**
3. Escolha **"Git Repository"**
4. Cole a URL do repositório (ex: `https://github.com/seu-usuario/book-scanner.git`)
5. Configure:
   - **Build Command**: `echo 'Ready'` (não precisa build)
   - **Start Command**: `python3 server.py`
   - **Port**: `8000`
   - **Environment**: deixe vazio ou adicione `NODE_ENV=production`

6. Clique em **"Deploy"** e pronto! ✅

## 📦 Alternativa com Docker

Se o Dokploy suportar Dockerfile:

1. No painel, escolha **"Docker"** em vez de Git
2. Aponte para o `Dockerfile` que preparei
3. Clique em **"Deploy"**

## 🔗 URL Final

Seu app estará em algo como:
```
https://seu-projeto-book-scanner.uatzap.com
```

Ou:
```
https://seu-projeto.dokploy.io
```

## ⚙️ Variáveis de Ambiente (Opcional)

Se quiser configurar no Dokploy, adicione na seção de Environment Variables:

```
PORT=8000
PYTHONUNBUFFERED=1
```

## 🐛 Se der erro:

### Erro: "Python not found"
- Dokploy pode precisar usar Node.js ou outra runtime
- Solução: Use a opção **"Static Files"** ou **"Docker"** em vez de Python direto

### Erro: "Port already in use"
- Dokploy atribui porta automaticamente
- O app ajusta dinamicamente via variável `PORT`

### App não responde
- Verifique os logs no painel do Dokploy
- Certifique-se que o arquivo `server.py` está no repositório

## 📊 Monitoramento

No painel do Dokploy você pode:
- Ver logs em tempo real
- Monitorar CPU/Memória
- Configurar Auto-deploy ao fazer push no Git
- Gerenciar domínios customizados

## 🎯 Resumo dos Arquivos

```
book-scanner/
├── book-scanner.html     # App principal (tudo que precisa)
├── server.py             # Servidor Python
├── Dockerfile            # Config Docker
├── dokploy.json          # Config específica Dokploy
├── README.md             # Instruções gerais
└── DEPLOY.md             # Este arquivo
```

---

**Pronto pra fazer deploy? Vá pro painel do Dokploy e é só seguir os passos! 🚀**
