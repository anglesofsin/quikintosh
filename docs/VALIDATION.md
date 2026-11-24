# Validação da exportação — 2026-11-24

Verificações realizadas no checkout exportado, sem automatizar a área de trabalho:

- 18 testes do roteador/seletor de shells passaram.
- 12 testes do backend e associações do Quick Look passaram.
- 14 testes do Dock passaram, usando o ambiente com Pillow.
- 3 testes do renderizador de ícones passaram, usando Pillow/NumPy/librsvg.
- Teste de instalação inicial dos padrões passou: cria arquivos em home temporário e preserva configurações existentes.
- Testes Node do companion passaram: entrada/saída de chamada, participantes, fala, controles, mute/deafen local, chamada de DM tocando e identidade Canary.
- Fontes Python dos integradores compiladas sem erros de sintaxe.
- Conferência do inventário: nenhum arquivo rastreado do upstream e nenhum arquivo de integração da rice ficaram ausentes.
- Fontes, flake e templates exportados não dependem dos checkouts pessoais `/home/pg/...`.
- Varredura de padrões comuns de tokens/chaves privadas não encontrou ocorrências; fotos de conta, histórico, caches, localização pessoal e credenciais não foram exportados.

As verificações de build e avaliação Nix desta entrega são registradas no commit após sua execução. A shell instalada no PC de desenvolvimento foi renomeada e seus IPCs responderam após a ativação.

Não foi feita instalação em um segundo computador físico, teste visual em outra GPU nem chamada real em todos os canais Discord nesta exportação. Os testes de voz são fixtures, não comprovação de uma chamada real em cada cliente. O módulo opcional de Discord requer a primeira reinicialização manual do cliente.
