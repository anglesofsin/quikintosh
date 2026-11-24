# Quickintosh

Rice completa para **NixOS + Hyprland**, inspirada no macOS Tahoe, baseada no Lickintosh e ampliada com Dynamic Island, Finder, Quick Look e Quickshot integrados.

Este repositório contém as fontes da shell, os assets do upstream, as modificações locais e as receitas Nix. Não depende dos checkouts `/home/pg/...` da máquina de desenvolvimento. O módulo instala a rice; não substitui a configuração de discos, bootloader, usuários ou senhas do seu sistema.

## O que está incluído

- **Menu Bar:** menus do aplicativo, troca por hover, cores automáticas/manuais, logo personalizável e cantos configuráveis.
- **Sons de notificação:** Rebound por padrão, alternativas/arquivo próprio, volume e controle por app; Não Perturbe silencia e interrompe os toques. Configure em Settings → Sound.
- **Dynamic Island:** notificações, música, chamadas, avatares e indicadores de fala, controles de chamada, privacidade, fullscreen e ocultação por inatividade.
- **Dock:** ocultação automática inteligente (fica visível na mesa e só se recolhe quando uma janela ocupa sua área), magnificação, apps instalados e recentes, bloqueio de apps nos recentes, Downloads/Recentes/Lixeira em pilhas, seleção múltipla, arrastar arquivos e menus de contexto.
- **Apps macOS (opcional):** Darling em ambiente persistente, biblioteca de `.app`, instaladores `.dmg`/`.pkg` e atalhos integrados. Compatibilidade experimental; [instalação e limites](docs/MACOS-APPS.md).
- **Finder:** Nautilus com tema Tahoe, sidebar e controles translúcidos, previews e integração ao Quick Look.
- **Quick Look / Quickview:** imagens, GIFs, vídeos, áudio, texto e outros formatos suportados; navegação, zoom, controles de mídia e Liquid Glass. Espaço/Esc/clique fora fecham a prévia.
- **Quickshot:** seleção de região, captura de monitor, edição, OCR para o clipboard, color picker, paleta, QR, régua, lupa e gravação. Capturas são salvas na Mesa por padrão.
- **Mesa e widgets:** fotos/GIFs, relógios personalizáveis, clima, estilos de fundo e edição por arrastar; tamanho dos itens configurável.
- **Settings:** aparência, ícones claros/escuros/tintados, cores do wallpaper, Liquid Glass, som, rede, privacidade, clima compartilhado, widgets, Dock, hot corners e outras opções.
- **Idioma e escala:** português brasileiro com busca localizada e escala própria da shell de 75% a 200%; [como configurar](docs/LANGUAGE-AND-SCALE.md).
- **Temas dos aplicativos:** templates/Matugen ao trocar wallpaper, com restauração de preferências ao sair desta rice.
- **Hyprland:** atalhos por shell, janelas flutuantes com geometria persistida e patches do compositor necessários ao vidro e ao scrolling.
- **Troca de shell:** Quickintosh, Noctalia C++, Noctalia Legacy, Caelestia e eqSh, com roteamento dos atalhos compatíveis.

A implementação usa os recursos disponíveis no Linux; não é uma distribuição de macOS. O Finder é Nautilus tematizado, e seu efeito GTK não tem toda a refração do shader Quickshell. Chamadas com participantes/avatares exigem o companion Discord; a detecção externa fornece apenas informações básicas. Veja [limitações e diagnóstico](docs/TROUBLESHOOTING.md).

## Arch Linux

Há um [instalador Arch com sessão isolada e guia para OpenCode](docs/ARCH.md). Ele usa pacman para serviços do host e Nix para o bundle da rice, sem converter o Arch em NixOS. Leia o guia, o diagnóstico de GPU e as limitações antes de instalar.

## Instalação NixOS: módulo

Arquitetura testada: **x86_64-linux**. É necessário usar flakes. A primeira compilação pode ser demorada: inclui o compositor modificado e componentes que podem não estar disponíveis no cache binário.

1. Dê acesso ao repositório à conta que fará a instalação. Se ele for privado, use um clone SSH autenticado. Não coloque tokens em arquivos Nix.
2. Clone:

   ```sh
   git clone git@github.com:anglesofsin/quikintosh.git ~/quickintosh
   ```

3. Integre o input e o módulo à sua flake NixOS. Exemplo completo em [examples/flake.nix](examples/flake.nix). Trecho principal:

   ```nix
   inputs.quickintosh.url = "git+ssh://git@github.com/anglesofsin/quikintosh.git";
   # Use o mesmo nixpkgs testado pela rice:
   inputs.nixpkgs.follows = "quickintosh/nixpkgs";
   ```

   Adicione `inputs.quickintosh.nixosModules.default` à lista `modules` do seu host e configure:

   ```nix
   quickintosh = {
     enable = true;
     user = "seuusuario"; # deve existir em users.users
     # Opcional: Discord com companion compilado junto.
     discord = { enable = true; clients = [ "canary" ]; };
   };
   ```

   Para um clone local, use `inputs.quickintosh.url = "path:/caminho/absoluto/quickintosh";`. Não substitua seu `hardware-configuration.nix` pelo de outra máquina. Se já gerencia Hyprland com Home Manager, retire a geração concorrente de `~/.config/hypr/*.lua` antes de aplicar este módulo.

4. Compile antes de ativar:

   ```sh
   sudo nixos-rebuild build --flake /caminho/da/sua/flake#seuhost
   sudo nixos-rebuild switch --flake /caminho/da/sua/flake#seuhost
   ```

5. Entre em uma sessão **Hyprland** pelo seu display manager. O módulo mantém seu gerenciador de login atual. Em uma primeira instalação sem display manager, configure o método de login de sua preferência antes de sair da sessão.
6. Selecione a shell:

   ```sh
   rice-shell switch quickintosh
   rice-shell status
   ```

Os arquivos Hyprland existentes com o mesmo nome são substituídos por links da configuração Nix durante a ativação. Faça backup de `~/.config/hypr` e `~/scripts` antes da primeira instalação; a ativação também fornece os scripts usados pelos atalhos. Não use este módulo simultaneamente com outro gerador desses mesmos arquivos.

## Configuração inicial e uso

- Coloque wallpapers em `~/Pictures/Wallpapers`; selecione-os em Settings → Wallpaper.
- Os padrões visuais desta rice são aplicados somente quando a configuração da shell ainda não existe. Suas alterações posteriores são preservadas.
- Nome do usuário, foto, localização do clima, contas e chaves de IA são configurados no seu próprio PC. Não são copiados da máquina de desenvolvimento.
- `quickintosh` é o comando público. Os diretórios `~/.config/lickintosh`, `~/.cache/lickintosh` e alguns identificadores internos são mantidos para compatibilidade com o upstream e com instalações anteriores.
- `quickintosh-finder` abre o gerenciador; `quickintosh-quicklook arquivo` abre a prévia.
- Ao mudar de rice pelo `rice-shell`, o perfil restaura aparência e associações capturadas anteriormente. Sair apenas matando o processo não equivale à troca gerenciada.

| Atalho | Função na Quickintosh |
| --- | --- |
| Super+P | Spotlight |
| Alt+P | Launchpad |
| Super+V | Clipboard |
| Super+L | Bloquear |
| Super+Shift+S | Captura de região / Quickshot |
| Print | Captura de monitor |
| Super+O | Quickshot |
| Super+Shift+O | OCR de região |
| Super+Shift+P | Captura com edição |
| Super+Shift+W | Wallpapers |
| Super+Shift+E | Editar widgets |
| Super+Alt+I | Assistente de IA |
| Super+Alt+G | Game Mode |
| Super+Alt+K | Keep Awake |
| Alt+Tab / Alt+Shift+Tab | Alternar apps |
| Espaço em arquivo | Quick Look |
| Ctrl+A na Mesa | Selecionar tudo |
| Ctrl+scroll na Mesa | Tamanho dos itens |
| Super+Shift+F5 | Reiniciar a shell |

A configuração completa é [modules/hyprland-lua/hyprland.lua](modules/hyprland-lua/hyprland.lua). Atalhos não compatíveis com a shell ativa não são registrados; atalhos de ações não fazem troca automática de shell.

## Discord e chamadas

Leia [docs/DISCORD.md](docs/DISCORD.md): instalação declarativa de Canary/PTB/Stable, Equibop, mods existentes, Shade, reinicialização inicial, privacidade e diagnóstico. O companion não precisa de token Discord e não captura áudio.

## Desenvolvimento e verificação

```sh
cd ~/quickintosh
nix build .#quickintosh          # shell e integrações completas
nix build .#rice-shell          # seletor de shells
nix flake check --no-build      # avalia a configuração NixOS de exemplo
python3 -m unittest discover -s tests/nix-cli -p test_rice_shell.py
```

Os testes de Quick Look, Dock, privacidade, ícones, wallpapers e voz ficam junto dos respectivos componentes em `modules/lickintosh/`. Alguns exigem Pillow, PyGObject, NumPy ou websockets; use o ambiente Python declarado na receita correspondente. Os testes Node da voz não abrem o Discord:

```sh
node modules/lickintosh/voice/test-renderer.cjs
node modules/lickintosh/voice/test-store-discovery.cjs
```

Veja [arquitetura e fontes](docs/ARCHITECTURE.md), [temas](docs/THEMING.md) e [validação desta exportação](docs/VALIDATION.md). Builds não substituem testes visuais em cada GPU/monitor.

## Licenças

Código derivado da shell sob GPL-3.0-or-later; componentes de terceiros mantêm suas licenças. Consulte [LICENSE](LICENSE), [THIRD_PARTY.md](THIRD_PARTY.md), `upstream/lickintosh/THIRD_PARTY_LICENSES/` e os avisos nos assets. Marcas Apple/macOS pertencem aos seus titulares; este projeto não é afiliado à Apple.

Desktop widgets support Liquid Glass, solid and transparent surfaces, plus per-widget overrides. Photo widgets preserve full color and accept images/GIFs, additional portrait/wide formats, fit modes and shapes. Hold Control while dragging a desktop widget for free placement and intentional overlap; configure this in Desktop & Dock. Desktop context menus use an overlay above the Dock, including secondary displays and Game Mode.

The desktop presents Finder menus (File, Edit, View, Go, Window and Help). Desktop actions use the shell file services; Finder window actions use the file manager shortcuts, with direct navigation to common folders. Voice call buttons preserve the original glyph artwork and center its visible bounds.

To resize a compatible desktop widget, choose **Resize Widget** from its context menu, or open Edit Widgets. Drag the right, bottom or corner handle to change width, height or both; hold Control to allow overlap. Custom dimensions persist, and choosing a preset size resets them. The personal clock supports automatic text scaling, larger presets, the lock screen font styles and glass shader, gradients, shadows, digit transitions, alignment and custom time/date formats. Its editor keeps the completion buttons visible and yields focus/stacking to native file choosers.

Resize handles dismiss after releasing the mouse, clicking the desktop, pressing Escape or leaving the desktop. Widget gallery previews wrap into rows instead of cropping wide presets. Discord Stable, Canary, PTB and Equibop have separate Dock identities even when they advertise the same window class; identification reads executable metadata and never restarts a client.
