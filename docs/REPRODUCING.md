# Reconstruir o Hyprland e a Quickintosh

O ponto de recuperação desta revisão é a tag **`desktop-rebuild-2026-11-27`**, na branch **`feat/droppy-island-surface`** do repositório `anglesofsin/quikintosh`. O `main` não contém todas as mudanças desta revisão. A tag fixa as fontes; `flake.lock` fixa os inputs e as versões compatíveis do compositor e das dependências.

Este guia reconstrói o ambiente gráfico e suas integrações. Ele não substitui o sistema específico de discos, bootloader, GPU, usuários e rede de outra máquina. A instalação não depende dos diretórios temporários usados durante o desenvolvimento.

## O que está versionado

| Parte | Fontes e receita |
|---|---|
| Hyprland, atalhos, fullscreen/maximização, workspaces normais e especiais | `modules/hyprland-lua/`, `modules/hyprland.nix`, `modules/infinite-desktop/` |
| Patches do compositor e versão compatível | `nix/overlay.nix`, `modules/hyprland-0.57-*.patch`, `flake.lock` |
| Shell, painéis, Settings e personalização | `upstream/lickintosh/`, integradores em `modules/lickintosh/`, ordem de montagem em `modules/rice.nix` |
| Liquid Glass e correções das transições | `modules/lickintosh/compositor/hyprglass.nix` e patches referenciados por essa receita |
| Telemetria, proteção de foco e contorno maximizado | `modules/lickintosh/rendering/geometry/` |
| Dynamic Island, ícones, menus, widgets e utilitários | `modules/lickintosh/island-shelf/`, `island-dashboard/`, fontes, assets e integradores relacionados |
| Finder, Enter para renomear, portal e Quick Look | `finder/`, `finder-portal/`, `desktop-files/`, `quicklook/` sob `modules/lickintosh/` |
| Wallpaper animado, extração de quadro e cores | `live-backdrop/`, `wallpaper-theme/`, `display-wallpaper/` |
| Perfil visual opcional da revisão | `profiles/current-desktop/profile.json` |
| Instalação NixOS / Arch | `nix/module.nix`, `examples/flake.nix`, `arch/`, `docs/ARCH.md` |
| Diagnóstico e testes | `scripts/check-rebuild.py`, `tests/`, testes dos componentes e `docs/reviews/` |

As fontes vendorizadas incluem seus assets, fontes, shaders e licenças. Não são submódulos que precisem ser encontrados em outro checkout local. Os inputs externos são obtidos pelas receitas Nix. Dependências externas ainda precisam estar disponíveis em seus servidores ou caches; Git não guarda todos os binários do Nix store.

## 1. Salvar o que é pessoal

Antes de reinstalar, preserve seu próprio `hardware-configuration.nix`, a flake do host e os arquivos pessoais. O GitHub contém o código e o perfil visual sanitizado; não contém uma cópia das suas contas ou da sua pasta pessoal.

Arquivos que exigem um backup **local separado**, quando quiser restaurá-los:

- `~/.config/lickintosh/`: configurações pessoais, widgets com conteúdo, notas, alarmes e histórico da ilha.
- `~/.local/state/quickintosh/island-shelf/`: referências da bandeja, preferências e dados dos utilitários. Os arquivos originais referenciados pela bandeja precisam ser salvos separadamente.
- `~/.config/kitty/` e personalizações adicionais de outros aplicativos.
- Wallpapers, vídeos, fotos, avatares, arquivos do usuário e scripts próprios que não fazem parte do projeto.
- Credenciais/pareamentos do KDE Connect, keyring, chaves de provedores de IA, contas e sessões dos aplicativos.
- Configurações do Spicetify/Spotify, extensões de aplicativos e modelos externos opcionais que você usa.

Não é necessário preservar `~/.local/state/quickintosh/active-review`, `/tmp/qi-*` ou caminhos `/nix/store/...` anotados em relatórios antigos. Eles descrevem os builds e ativações da máquina de desenvolvimento. As fontes e receitas no repositório substituem essa dependência. Capturas locais citadas em relatórios também não são necessárias para compilar a interface.

### Síntese de voz opcional

O caminho padrão de `say.sh` usa o eSpeak NG instalado pelo módulo. Os helpers opcionais do Kokoro, inclusive `setup-kokoro.sh` e `kokoro/shell.nix`, também estão versionados. O ambiente Nix desse helper usa uma revisão/hash fixos. Sua instalação Python/modelos via rede e um servidor RVC externo não fazem parte do build básico da interface; preserve seus próprios modelos/configurações se os usa. Esta revisão não executou nem validou novamente a instalação dos modelos opcionais.

## 2. Obter a revisão certa

```sh
git clone --branch feat/droppy-island-surface --single-branch \
  https://github.com/anglesofsin/quikintosh.git ~/quickintosh
cd ~/quickintosh
git fetch origin tag desktop-rebuild-2026-11-27
git checkout desktop-rebuild-2026-11-27
git status --short
python3 scripts/check-rebuild.py
```

Se o repositório exigir autenticação, use seu acesso GitHub/SSH. Nunca escreva tokens dentro da flake. A saída vazia de `git status --short` confirma que o checkout não tem alterações locais; o verificador examina os inputs relativos rastreados e os scripts dos atalhos, mas não substitui um build.

## 3. Compilar sem alterar a sessão

Em x86_64 Linux com Nix e flakes habilitados:

```sh
nix build .#shell-source --no-link --print-out-paths
nix build .#glass-plugin .#geometry-plugin .#finder-theme --no-link
nix build .#quickintosh .#hyprland .#hyprland-config --no-link
nix flake check --no-build
```

`#shell-source` monta os QML, Python, assets e alterações na ordem real de produção. Os outros alvos compilam os plugins e wrappers correspondentes. Não copie para outra instalação os `.so` de uma sessão antiga: Hyprland e os plugins devem ser construídos pelo mesmo lock e toolchain. O carregador verifica a compatibilidade; não contorne uma rejeição de ABI.

Um build completo pode precisar baixar dependências e compilar o compositor, GTK, Rust ou componentes Qt. Falta de espaço/inodes, indisponibilidade de upstream e falta de rede podem impedir o build e devem ser tratadas como falhas, não como instalação concluída.

## 4. Instalar no NixOS

Use [examples/flake.nix](../examples/flake.nix) como referência. Mantenha os módulos do seu próprio host e importe `inputs.quickintosh.nixosModules.default`. Para usar a tag fixa no input:

```nix
inputs.quickintosh.url = "git+https://github.com/anglesofsin/quikintosh.git?ref=desktop-rebuild-2026-11-27";
inputs.nixpkgs.follows = "quickintosh/nixpkgs";
```

Na configuração do host:

```nix
quickintosh = {
  enable = true;
  user = "seuusuario";
  discord = { enable = true; clients = [ "canary" ]; };
};
```

Atualize o lock da flake do host para registrar esse input. Se já usa Home Manager ou outro gerador de Hyprland, retire a geração concorrente dos mesmos arquivos antes de ativar. O módulo instala links em `~/.config/hypr` e os helpers em `~/scripts`; preserve mudanças pessoais que existam nesses destinos.

```sh
sudo nixos-rebuild build --flake /caminho/da/flake-do-host#seuhost
sudo nixos-rebuild switch --flake /caminho/da/flake-do-host#seuhost
```

Entre na sessão Hyprland pelo seu método de login e selecione a interface:

```sh
rice-shell switch quickintosh
rice-shell status
```

Para o KDE Connect em uma instalação NixOS nova, confira também `programs.kdeconnect.enable = true` no host e faça novamente o pareamento; instalar o cliente sem liberar a descoberta na rede pode impedir que o celular apareça. Aplicativos pessoais como Spotify e navegadores continuam sendo responsabilidade dos pacotes do seu host, salvo os clientes Discord habilitados pela opção acima.

Não é preciso instalar o plugin manualmente ou recriar os scripts temporários de revisão. O wrapper carregará os plugins e a shell montados pela receita. O módulo não substitui bootloader, discos, senhas ou o método de login.

## 5. Restaurar o perfil visual desta revisão

O perfil é **opcional**. Os padrões genéricos continuam em `defaults/`. Para conferir o que o perfil alterará:

```sh
cd ~/quickintosh
python3 scripts/visual-profile.py restore profiles/current-desktop/profile.json
```

Para aplicar:

```sh
python3 scripts/visual-profile.py restore profiles/current-desktop/profile.json --apply
```

O script salva os arquivos anteriores em `~/.local/state/quickintosh/profile-backups/<data>/`, mescla as preferências JSON e usa gravação atômica. Ele não reinicia aplicativos. Reabra Settings e a shell pelo fluxo normal; reabra o Kitty para que ele leia opacidade, margens e cores restauradas.

O perfil inclui parâmetros da ilha, aparência, cantos, Dock, navegação, ícones contextuais, opções de vidro, idioma/escala e a configuração visual do Kitty. A transparência do terminal depende tanto da configuração do Kitty quanto do plugin — instalar apenas o plugin não recria essa parte do visual.

Não inclui textos privados, pastas/arquivos fixados, servidores, histórico, conteúdo de widgets, notas, localização do clima, foto, arquivos de wallpaper ou chaves. Portanto, não promete reproduzir seus dados pessoais ou cada pixel de um wallpaper ausente. Se quiser exportar outro perfil visual sanitizado:

```sh
python3 scripts/visual-profile.py export /caminho/do/perfil-visual.json
```

Para desfazer, pare a interface antes de restaurar os arquivos correspondentes do diretório de backup, preservando também eventuais edições posteriores. Arquivos que não existiam antes da importação não têm cópia anterior no backup.

## 6. Conferência após a instalação

- Mesa vazia mostra Finder na menubar; confira também a saída de uma special workspace.
- Alt+F maximiza e restaura a organização; fullscreen solicitado pelo aplicativo continua funcionando.
- Dock oculta/exibe e amplia ícones ao arrastar arquivos; painéis e widgets mantêm o vidro vivo.
- Settings abre cada página; a busca encontra controles e restaurar teclado não apaga ajustes do mouse/compositor.
- Enter renomeia na Mesa/Finder; Espaço abre Quick Look e Escape fecha.
- Música, fila suportada, player flutuante e chamadas Discord usam as integrações documentadas.
- Wallpaper animado: confira reprodução, limites opcionais e paleta pelo primeiro quadro.
- Troque workspaces com dois terminais transparentes. As correções de borda e amostragem estão incluídas; o relato visual residual da máquina original ainda exigia confirmação do usuário na data desta revisão.

Para problemas, veja [TROUBLESHOOTING.md](TROUBLESHOOTING.md), [DISCORD.md](DISCORD.md), [NATIVE-GLASS-RUNTIME.md](NATIVE-GLASS-RUNTIME.md) e os relatórios de revisão. Um teste isolado não garante comportamento de outra GPU, monitor, dispositivo de áudio ou autenticação.

## Arch e outros sistemas

No Arch use [docs/ARCH.md](ARCH.md) e o bundle `#arch`, com os serviços do host e wrappers de GPU indicados ali. Não execute `nixos-rebuild` no Arch. Outras distribuições não foram validadas como instalações completas por esta revisão.
