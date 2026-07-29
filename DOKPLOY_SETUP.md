# 🌐 Setup Dokploy com Domínio parabola.gabsdev.com

Guia passo a passo para colocar sua app em produção no Dokploy.

## ✅ Pré-requisitos

- ✅ Repositório Git (GitHub, GitLab, etc)
- ✅ Acesso ao Dokploy
- ✅ Acesso ao DNS (registrar domínio)

---

## 🚀 PASSO 1: Prepare o Repositório

### 1.1 Inicializar Git

```bash
cd /Users/g/Downloads/parabola
git init
git add .
git commit -m "🚀 Initial commit: Book Scanner App"
```

### 1.2 Criar Repositório no GitHub

1. Vá para https://github.com/new
2. Nome: `book-scanner`
3. Descrição: `📚 Real-time barcode reader for books`
4. Clique em "Create repository"

### 1.3 Push do Código

```bash
git remote add origin https://github.com/seu-usuario/book-scanner.git
git branch -M main
git push -u origin main
```

---

## 🐳 PASSO 2: Deploy no Dokploy

### 2.1 Acessar Painel Dokploy

1. Abra: https://panel.uatzap.com/dashboard
2. Faça login com suas credenciais

### 2.2 Criar Novo Projeto

1. Clique em **"New Project"** (ou ⭐ Create)
2. Escolha: **"Git Repository"**
3. Preencha:
   - **Repository URL**: `https://github.com/seu-usuario/book-scanner.git`
   - **Branch**: `main`
   - **Build Directory**: `.` (ponto)

### 2.3 Configurar Deploy

Na seção **"Build & Deploy"**:

```
Build Command:    echo "Ready to deploy"
Start Command:    python3 server.py
Publish Directory: .
Port:             8000
```

### 2.4 Environment Variables

Deixe vazio ou adicione:
```
PORT=8000
PYTHONUNBUFFERED=1
```

Clique em **"Save"** → **"Deploy"**

---

## 🌐 PASSO 3: Configurar Domínio

### 3.1 Apont DNS

Em seu gerenciador de domínio (GoDaddy, Namecheap, etc):

1. Vá para **DNS Records**
2. Crie um registro **CNAME**:
   - Nome: `parabola`
   - Aponta para: `seu-projeto.dokploy.io` (você vê isso no painel)

### 3.2 No Painel Dokploy

1. Vá para o projeto criado
2. Clique em **"Domains"**
3. Adicione: `parabola.gabsdev.com`
4. Ative **"SSL/TLS"** (Let's Encrypt automático)
5. Clique em **"Save"**

**Espere 5-10 minutos** para DNS propagar.

### 3.3 Acessar a App

```
https://parabola.gabsdev.com
```

✅ Pronto! App ao vivo!

---

## ⚙️ CONFIGURAÇÃO AVANÇADA (Opcional)

### Auto-Deploy ao fazer Push

No painel Dokploy:

1. Vá para **Settings** do projeto
2. Ative **"Auto Deploy"**
3. Agora cada `git push` faz deploy automaticamente! 🎯

### Variáveis de Ambiente

Se precisar adicionar dados de API:

```
BOOKS_API_URL=https://api.exemplo.com
API_KEY=seu-api-key
```

Acesse via `os.getenv('BOOKS_API_URL')` no Python.

---

## 📊 MONITORAMENTO

No painel Dokploy você pode:

- 📊 Ver uso de CPU/Memória
- 📋 Ler logs em tempo real
- 🔄 Reiniciar aplicação
- 🗑️ Ver histórico de deploys
- 📱 Gerenciar domínios

---

## 🐛 TROUBLESHOOTING

### "Build Failed"
- Verifique se `book-scanner.html` e `server.py` estão no repositório
- Confirme que `Dockerfile` está correto
- Veja logs do build no painel

### "Domain not working"
- Espere 10-15 min para DNS propagar
- Verifique registros DNS no seu gerenciador
- Confirme que domínio foi adicionado no Dokploy

### "Connection refused"
- Verifique se porta 8000 está exposta
- Confirme que `server.py` está rodando
- Veja logs no painel

### "Permissão de câmera recusada"
- App precisa HTTPS (Let's Encrypt no Dokploy já faz isso)
- Aceite permissão quando navegador pedir

---

## 📈 PRÓXIMOS PASSOS

- [ ] Fazer deploy (seguir passo 1-3)
- [ ] Testar app em produção
- [ ] Configurar auto-deploy
- [ ] Adicionar mais livros na base de dados
- [ ] Integrar com API de preços real
- [ ] Customizar branding

---

## 💡 DICAS

**Se quiser rodar localmente enquanto testa:**
```bash
python3 server.py
# Depois abra: http://localhost:8000/book-scanner.html
```

**Para adicionar novos livros sem fazer novo deploy:**
- Edite `book-scanner.html` direto no GitHub
- Ative auto-deploy
- As mudanças refletem em segundos!

**Se quiser cache customizado:**
- Adicione header `Cache-Control` no `server.py`
- Ou configure no Dokploy (Settings → Cache)

---

## ✅ CHECKLIST FINAL

- [ ] Repositório criado no GitHub
- [ ] Código fez push para `main`
- [ ] Projeto criado no Dokploy
- [ ] Build command configurado
- [ ] Deploy realizado com sucesso
- [ ] Domínio `parabola.gabsdev.com` adicionado
- [ ] DNS apontando corretamente
- [ ] App acessível via HTTPS
- [ ] Câmera funcionando no mobile
- [ ] Código de barras sendo detectado

---

## 🎉 VOCÊ TEM TUDO PRONTO!

Sua app está online em:
```
https://parabola.gabsdev.com
```

**Compartilhe com seus amigos e comece a ler códigos de barras de livros em tempo real!** 📚📱💰

---

**Dúvidas?** Leia logs no painel ou edite o código e faça novo push! 🚀
