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

## Relógio com geometria estável

O componente real de relógio passou por 48 combinações de horário, incluindo segundos, 12 horas, formato empilhado, tamanho automático e fonte personalizada. O tamanho ajustado da fonte permaneceu constante dentro de cada configuração; os algarismos tabulares e a ausência de zoom/estiramento na transição também foram conferidos. Em uma sessão gráfica isolada, desligar a preferência global ocultou o relógio nos estados de música e chamada, preservando sua largura reservada.

## Música compacta e tray adaptativa

- A pill de música usa a mesma altura configurada para chamada/inatividade, sem a margem externa adicional de 26 px. Capa circular e visualizador ficam nas extremidades com margens de 3/4 px; o espaço reservado ao relógio continua disponível quando ele está oculto.
- A capa gira no renderizador, sem capturas de tela por frame, e respeita pausa/redução de movimento. O teste gráfico isolado conferiu altura de 26 px e capa circular de 20 px, comparadas com o estado de chamada.
- A tray analisa uma imagem de 32 px apenas quando o ícone muda. O teste Qt verificou ícones brancos/pretos, preservação de imagem colorida e atualização da cor da barra. Também foram lidos os ícones reais publicados pelo Discord, Canary e Steam em uma janela de teste fora da tela principal.
- Após a checagem de integração detectar uma importação ausente no consumidor da tray, ela foi corrigida e a shell completa carregou com sucesso em uma sessão gráfica isolada. As verificações de componente isolado não foram usadas como substituto dessa checagem completa.

## Espessura estável na música

O estado compacto de música agora tem pelo menos 30 px de altura (4 px acima da altura configurada), capa de 20 px na configuração padrão e margens externas de 7 px nos dois lados. A borda pulsante, o halo reativo e a deformação elástica são desativados nesse estado; o visualizador continua reagindo ao áudio. O componente real foi renderizado em sessão isolada, comparado com a chamada de 26 px e exercitado com `beat` alternando entre 0 e 1 sem mudar altura ou margens.

## Espaçamentos da ilha e galeria simplificada

A altura da música voltou a seguir a altura configurada da ilha, preservando a remoção das deformações reativas. A apresentação na menubar mantém afastamento mínimo de 4 px do topo; a capa e o visualizador mantêm 6 px de margem lateral. O teste gráfico mediu 26 px de altura e margens iguais de 3 px à esquerda/acima/abaixo do avatar da chamada. A galeria de imagens oferece uma única entrada, mantendo todos os tamanhos, formatos e redimensionamento no editor. O relógio da ilha passa a vir desligado no padrão de novos perfis; preferências persistidas não são sobrescritas.
O fechamento agora retira as atividades laterais no início da ocultação (incluindo fullscreen e ocultação por inatividade), antes de a pill principal terminar de encolher. O campo de fusão das bolinhas é atualizado junto, evitando contornos residuais.
