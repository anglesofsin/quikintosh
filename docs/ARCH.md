# Arch Linux: instalação assistida pelo OpenCode

O suporte Arch usa **pacman para os serviços do sistema e Nix para a rice**. O Arch continua sendo Arch; não é necessário reinstalar o sistema nem usar `nixos-rebuild`. Não é um PKGBUILD/AUR nativo: Nix mantém juntos a versão modificada de Hyprland, o plugin, o portal, Quickshell/Qt e todas as integrações que esta rice exige.

**Estado:** instalador e bundle implementados, build e testes locais descritos em `ARCH-VALIDATION.md`. Ainda precisa de teste gráfico no hardware Arch da pessoa que instala. Não foi validado em todos os drivers NVIDIA/GPUs híbridas. O instalador não encerra nem substitui a sessão gráfica existente.

## 1. Preparação

Requisitos: Arch ou derivada com systemd, arquitetura x86_64, acesso a sudo e ao repositório, espaço livre para o Nix store e conexão para baixar/compilar os componentes. Reserve dezenas de GB; a primeira compilação pode ser longa. Use o driver de vídeo já apropriado à máquina. Não misture o plugin daqui com um Hyprland de versão diferente.

```sh
git clone git@github.com:anglesofsin/quikintosh.git ~/quickintosh
cd ~/quickintosh
# Leia o script; esta etapa usa pacman e mantém seus prompts normais.
sudo bash arch/system-setup.sh
```

A etapa de sistema faz uma atualização completa `pacman -Syu --needed`, instala Nix e serviços necessários e cria políticas PAM privadas para a tela de bloqueio, preservando políticas próprias do administrador. As referências aos módulos PAM usam caminhos absolutos do Arch, para não carregar inadvertidamente módulos/PAM helpers do Nix; os includes e controles do host são preservados. Reexecute a preparação após alterações relevantes do `pambase`. Pode haver perguntas/conflitos normais do pacman, por exemplo ao substituir PulseAudio por PipeWire; o OpenCode deve explicar e resolver isso com você, não forçar a remoção de pacotes. Não roda `--noconfirm` e não instala driver NVIDIA automaticamente.

Se já usa Nix/serviços equivalentes e prefere instalação manual, consulte o script para a lista exata de pacotes e os dois arquivos PAM. O método é compatível com a [instalação Nix via pacman](https://nix.dev/install-nix.html) e com a [ArchWiki](https://wiki.archlinux.org/title/Nix). Abra um novo terminal/login se o Nix ainda não estiver no PATH ou seu usuário não conseguir acessar o daemon. Habilite os serviços de áudio/rede/contas que quiser usar; o diagnóstico diferencia os ausentes.

## 2. Diagnosticar e instalar como usuário normal

```sh
./arch/install.sh doctor
./arch/install.sh install --graphics mesa
```

`mesa` é a escolha para Intel/AMD com Mesa. Para NVIDIA proprietário:

```sh
./arch/install.sh install --graphics nvidia
```

NVIDIA usa a detecção impura do nixGL para o driver instalado no host. Se ela falhar ou o computador usar GPU híbrida, pare no diagnóstico e ajuste a configuração de GPU antes de iniciar a sessão. A versão do driver do kernel e as bibliotecas de usuário precisam ser compatíveis. `--graphics none` existe para máquinas em que a integração gráfica do Nix já esteja configurada; não use como solução cega para uma falha de driver.

O build usa os inputs fixados na flake; não exige habilitar flakes globalmente, pois o instalador passa as opções necessárias em cada chamada. Não instale a rice inteira como root: os arquivos pertencem ao usuário da sessão.

O instalador:

- compila/baixa `.#arch` e o wrapper gráfico;
- preserva `~/.config/hypr` e os scripts atuais;
- cria configuração própria em `~/.config/quickintosh/hypr` e scripts em `~/.local/share/quickintosh/scripts`;
- instala comandos em `~/.local/bin`, com backup de comandos existentes de mesmo nome;
- mantém uma geração e um registro de instalação em `~/.local/state/quickintosh-arch`;
- registra o portal compatível como unidade de usuário, ativada pela sessão;
- não inicia a shell, não mata seu desktop e não ativa lockscreen para testá-la.

Se um arquivo gerenciado foi editado, uma atualização para e preserva o arquivo em vez de sobrescrevê-lo. Uma falha de ativação reverte as escritas daquela tentativa. Preferências pessoais da shell permanecem em `~/.config/lickintosh`; o nome é mantido por compatibilidade.

## 3. Entrar na sessão

Para adicionar uma entrada ao display manager:

```sh
./arch/install.sh register-session
```

Isso solicita sudo apenas para copiar uma entrada para `/usr/share/wayland-sessions/quickintosh-UID.desktop`. Sua entrada atual continua disponível. Faça logout quando for conveniente e escolha **Quickintosh** no seletor de sessões. Não tente carregar a configuração Lua desta rice no Hyprland Arch já em execução.

Alternativamente, após sair do desktop, entre em um TTY e execute:

```sh
~/.local/bin/quickintosh-session
```

O launcher recusa iniciar por cima de uma sessão com DISPLAY/WAYLAND_DISPLAY. Ele inicia o compositor fixado com a configuração isolada; por isso não precisa substituir o pacote Hyprland do pacman. PATH e variáveis Qt são preparados pelo launcher. Não copie os exports de bibliotecas Nix/Qt para `.profile` ou `.bashrc` globalmente.

## 4. Checklist do primeiro teste

Dentro da sessão:

```sh
~/.local/bin/quickintosh-doctor
~/.local/bin/rice-shell status
~/.local/bin/quickintosh ipc call quicklook status
~/.local/bin/quickintosh ipc call capture status
~/.local/bin/quickintosh ipc call voice status
```

Teste um item de cada vez: Spotlight (Super+P), Launchpad (Alt+P), clipboard (Super+V), captura (Super+Shift+S), som, Finder, Quick Look, ícones e widgets. Wallpapers: `~/Pictures/Wallpapers`.

Teste manualmente o bloqueio/desbloqueio apenas quando puder usar sua senha e um TTY de recuperação. PAM usa a política do Arch, não a do NixOS. Antes de depender de bloqueio automático, confirme que o desbloqueio realmente funciona no seu host.

Confira captura/compartilhamento no navegador. O processo `quickintosh-session-ready` atualiza o ambiente D-Bus/systemd de usuário e inicia o portal compatível. Se houver falha:

```sh
systemctl --user status quickintosh-portal-hyprland.service xdg-desktop-portal.service
journalctl --user -b -u quickintosh-portal-hyprland.service -u xdg-desktop-portal.service --no-pager
```

A configuração de portal desta sessão fica em `~/.config/xdg-desktop-portal/quickintosh-portals.conf`. Saia completamente da sessão antes de testar outra sessão gráfica. Um portal antigo pode exigir reiniciar os serviços de usuário da nova sessão.

## 5. Discord

O Arch não usa a opção `quickintosh.discord` do módulo NixOS. Instale/use seu Discord ou Equibop normalmente e siga [DISCORD.md](DISCORD.md), seções de mod existente/Equibop/Shade:

```sh
~/.local/bin/quickintosh-discord-install
# ou, para um renderer gravável já pertencente ao mod:
~/.local/bin/quickintosh-discord-install --renderer /caminho/do/mod/renderer.js
```

Depois reinicie o cliente manualmente quando puder interromper a chamada. Sem companion a detecção externa é limitada. A instalação do companion não baixa Shade nem inclui plugins privados.

## 6. Atualizar e remover

Atualização, sem trocar de sessão automaticamente:

```sh
cd ~/quickintosh
git pull
./arch/install.sh install --graphics mesa # ou nvidia, conforme a instalação
```

Reentre na sessão para usar a nova geração do compositor. Não faça reload de um plugin novo no compositor antigo. Se atualizar o driver NVIDIA do Arch, reconstrua o wrapper gráfico correspondente.

Para remover, saia da Quickintosh e entre na sessão anterior/TTY:

```sh
cd ~/quickintosh
./arch/install.sh uninstall
sudo rm -f "/usr/share/wayland-sessions/quickintosh-$(id -u).desktop"
```

O uninstall restaura comandos/configurações anteriores quando os arquivos gerenciados estão intactos. Arquivos modificados depois da instalação são preservados e listados. Preferências pessoais, backups, gerações e pacotes do sistema/Nix não são apagados automaticamente. Se houve crash antes de restaurar o perfil visual, rode `~/.local/bin/lickintosh-desktop-profile leave` antes do uninstall. Não desinstale Nix se você também o usa para outros programas.

## Limitações que o OpenCode deve considerar

- Este suporte reutiliza o bundle Nix; não foi implementada uma segunda compilação nativa completa para pacman/AUR.
- [Programas gráficos Nix fora do NixOS](https://wiki.nixos.org/wiki/Nixpkgs_with_OpenGL_on_non-NixOS) exigem integração com os drivers. [nixGL](https://github.com/nix-community/nixGL) é o wrapper usado aqui. Algumas combinações de drivers e aplicações Arch abertas a partir de processos Nix precisam de ajustes de ambiente; teste aplicativos nativos também, não só a shell.
- Nem todos os desktops/display managers leem entradas de sessão do home, por isso existe `register-session`.
- Serviços opcionais (Bluetooth, AccountsService, keyring, rede, impressoras, brilho DDC/CI) dependem da configuração real do Arch. O instalador não substitui sua rede nem configura um driver proprietário.
- Settings consulta atualizações Arch por `pacman -Qu`; a atualização do sistema continua sendo feita por pacman, e a da rice pelo instalador. Recursos exclusivamente NixOS, como gerações do sistema, não existem no Arch.
- O home deve usar um caminho sem espaços ou caracteres especiais de shell para os atalhos/scripts herdados desta rice.

## Prompt pronto para o OpenCode

> Instale a Quickintosh deste repositório no meu Arch seguindo docs/ARCH.md e arch/README.md. Primeiro faça diagnóstico de GPU, serviços de áudio, Nix, acesso ao repositório e políticas PAM. Use o instalador Arch com Nix e a sessão isolada; preserve meu desktop/Hyprland atual e os backups. Não execute nixos-rebuild, não substitua meus discos/bootloader, não encerre minha sessão nem teste lockscreen sem eu estar pronta. Leia logs e corrija dependências antes de seguir; não ignore falhas. Depois me deixe entrar na sessão Quickintosh e teste comigo captura, clipboard, Finder/Quick Look, apps nativos, voz e desbloqueio. Explique limitações específicas do meu hardware.
