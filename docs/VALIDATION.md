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

- `nix build .#quickintosh` concluiu com sucesso, incluindo todos os integradores, fontes, ícones, Finder e Quick Look.
- `nix flake check --no-build` passou, inclusive a avaliação da configuração NixOS de exemplo.
- A opção Discord foi avaliada com Canary, PTB e Stable habilitados.
- Título da janela, identificação QML, backend e regra Hyprland do Quick Look foram conferidos após a renomeação.

A shell instalada no PC de desenvolvimento foi renomeada e seus IPCs responderam após a ativação. O status de voz real retornou Canary com metadados completos e controles disponíveis, sem reiniciar o cliente nesta tarefa.

Não foi feita instalação em um segundo computador físico, teste visual em outra GPU nem chamada real em todos os canais Discord nesta exportação. Os testes de voz são fixtures, não comprovação de uma chamada real em cada cliente. O módulo opcional de Discord requer a primeira reinicialização manual do cliente.

## Correções de widgets, ilha e imagens de chamada

- 15 testes Python do broker/cache de voz passaram, incluindo normalização de WebP, avatares padrão, cache offline e separação dos clientes.
- 12 regressões do grafo de captura passaram: microfone, monitor de áudio, câmera, tela, links pausados, stream suspenso e stream desabilitado.
- Os testes Node do renderer verificam nome/foto de uma DM antes de atender e atualizações locais de mute/deafen.
- Uma sessão Sway/Quickshell isolada confirmou que ocultar o relógio mantém a largura da ilha e que o fechamento da galeria preserva a seleção de estilo e não dessatura o widget. O relógio foi renderizado com a nova refração sobre o wallpaper; não houve erro de link do shader.
- O download real de um avatar padrão do CDN retornou PNG válido com o cabeçalho corrigido. Isso não substitui a validação de uma chamada real em todos os clientes ou de condições de rede de outra máquina.
- A página da Dynamic Island deixou de ter filtro interno; a busca geral das Settings permanece disponível. O ícone oficial amarelo do Canary tem identidade própria no banco e precedência sobre o arquivo genérico do Discord.
