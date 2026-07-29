# 📚 Leitor de Código de Barras de Livros

Uma aplicação web moderna que lê códigos de barras de livros em **tempo real usando a câmera do celular** e exibe o preço flutuando sobre o livro — tipo Google Tradutor! 

## ✨ Features

- 📷 **Câmera em tempo real** — acessa a câmera traseira do celular
- 🎯 **Detecção automática** de código de barras (EAN-13, EAN-8, UPC, etc)
- 💰 **Preço flutuante** — mostra o valor em card animado
- 📊 **Lista de detectados** — histórico dos últimos livros lidos
- 🎨 **UI moderna** — design limpo e responsivo
- ⚡ **Rápido** — roda 100% no navegador, sem back-end necessário
- 📱 **Mobile-first** — otimizado para celular

## 🚀 Como Usar

### 1. Iniciar o servidor

```bash
cd /Users/g/Downloads/parabola
python3 server.py
```

Você verá algo como:
```
🚀 Servidor iniciado!
📱 Acesse via navegador do celular:
   http://<seu-ip>:8000/book-scanner.html

💡 Para encontrar seu IP (Mac):
   ipconfig getifaddr en0
```

### 2. Abrir no celular

- Abra o navegador do celular (Chrome, Safari, etc)
- Digite: `http://<seu-ip>:8000/book-scanner.html`
- Exemplo: `http://192.168.1.100:8000/book-scanner.html`

### 3. Usar a app

1. Clique em **"📷 Câmera"** para ligar a câmera
2. Aponte para o **código de barras** do livro
3. Quando detectar, o **preço aparece flutuando** na tela
4. Os últimos livros detectados aparecem na lista abaixo

## 🛠 Personalização

### Adicionar mais livros

Abra `book-scanner.html` e localize esta seção:

```javascript
const bookDatabase = {
    '9788535914849': { title: 'Dom Casmurro', author: 'Machado de Assis', price: 34.90 },
    // Adicione mais aqui:
    '9788535914850': { title: 'Seu Livro', author: 'Seu Autor', price: 50.00 },
};
```

### Integrar com API

Para usar dados de uma API em vez de um banco local, substitua a função `processBarcode()`:

```javascript
async function processBarcode(barcode) {
    const response = await fetch(`https://sua-api.com/livros/${barcode}`);
    const bookInfo = await response.json();
    // ... resto do código
}
```

## 📊 Formatos de Código de Barras Suportados

- ✅ EAN-13 (padrão internacional de livros)
- ✅ EAN-8 (versão curta)
- ✅ UPC-A e UPC-E (padrão americano)
- ✅ Code 128
- ✅ Codabar

## 🔧 Tecnologias

- **HTML5/CSS3/JavaScript** — sem dependências externas pesadas
- **QuaggaJS** — detecção de código de barras via WebRTC
- **WebRTC** — acesso à câmera do dispositivo
- **Canvas API** — processamento de frames de vídeo

## 📝 Estrutura do Projeto

```
parabola/
├── book-scanner.html      # App principal (tudo em um arquivo)
├── server.py              # Servidor Python simples
└── README.md              # Este arquivo
```

## ⚠️ Permissões Necessárias

A app precisa de:
- ✅ **Câmera** — para ler códigos de barras
- ❌ **Microfone** — não usa
- ❌ **Localização** — não usa

Quando abrir no celular, o navegador pedirá permissão para acessar a câmera. **Clique em "Permitir"**.

## 🐛 Troubleshooting

### "Câmera desligada"
- Verifique se você permitiu acesso à câmera no navegador
- Tente recarregar a página
- Certifique-se que a câmera do celular funciona em outros apps

### Não detecta código de barras
- Aponte direto para o código de barras
- Deixe o código bem iluminado
- Não mexa na câmera enquanto digitaliza
- O código de barras precisa estar na base de dados

### Lento ou travado
- Feche outras abas do navegador
- Limpe o cache (Settings → Clear cache)
- Reinicie o navegador

## 📊 Próximas Melhorias

- [ ] Buscar preços em API de livros real (Google Books API, Skoob, etc)
- [ ] Exportar histórico de leitura
- [ ] Filtros por categoria/autor
- [ ] Modo offline com sincronização
- [ ] Notificações de promoções
- [ ] Integração com carrinho de compras

## 📄 Licença

MIT — Use como quiser!

---

**Desenvolvido com ❤️ por Claude Code**

Dúvidas? Abra uma issue ou me chame! 🎉
