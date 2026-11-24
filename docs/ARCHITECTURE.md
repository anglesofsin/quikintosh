# Arquitetura

`flake.nix` exporta o módulo NixOS e os pacotes. `flake.lock` fixa as revisões remotas. A árvore base do Lickintosh é vendorizada em `upstream/lickintosh`, incluindo fontes editáveis, shaders, assets e licenças; não é um binário opaco.

`modules/rice.nix` monta a shell aplicando os integradores em ordem: otimizações e vidro, Rosa, voz, captura, temas, Dock, Quick Look, Settings, widgets, privacidade, ícones e feedback. Essa ordem faz parte do build. A shell final é produzida no Nix store, sem depender de arquivos de desenvolvimento fora do checkout.

| Parte | Fonte |
| --- | --- |
| Dynamic Island | `modules/lickintosh/rosa-integrate.py`, `RosaPage.qml`, `voice/`, `island-idle-hide/`, input Rosa |
| Finder | `finder/`, `finder-glass.css`, `desktop-profile.py` |
| Quick Look | `quicklook/` |
| Quickshot | `capture/` |
| Dock e pilhas | `dock/` |
| Settings | `settings/`, `tahoe-unification/`, `appearance-polish/`, demais integradores |
| Widgets | `extra-widgets/`, `image-widget/`, `widget-motion/` e widgets upstream |
| Ícones | `layered-icons/`, `icon-styles/` |
| Temas de aplicativos | `theming/`, `defaults/` |
| Performance | `performance/`, `optimize.py`, `fluid-glass.py` |
| Hyprland/atalhos | `modules/hyprland-lua/`, `modules/infinite-desktop/` e patches |
| Seleção de shell | `modules/rice/rice-shell.py` |

Os caminhos abreviados na tabela são relativos a `modules/lickintosh/`, exceto onde indicado. O diretório mantém o nome upstream para que patches, imports e configurações existentes continuem funcionando; a marca visível e os comandos públicos são Quickintosh.

O overlay Nix fornece o Hyprland modificado e o portal compatível. O módulo exportado configura o usuário indicado em `quickintosh.user`, sem fixar o monitor, resolução ou nome de usuário do desenvolvedor. Não importa módulos pessoais de rede, WireGuard, discos ou serviços privados.

Os padrões de aparência ficam em `defaults/`, sanitizados. Não são exportados caches, históricos de clipboard, chamadas, recentes, fotos de perfil, contas, senhas ou a biblioteca pessoal de wallpapers. Assets de exemplo do upstream permanecem disponíveis.
