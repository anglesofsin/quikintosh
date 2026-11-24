# Diagnóstico e remoção

## Shell ou atalhos

```sh
rice-shell status
rice-shell capabilities
quickintosh ipc call quicklook status
quickintosh ipc call capture status
quickintosh ipc call voice status
```

Log: `~/.local/state/nixos-rice/shell.log`. Reinicie a shell com `rice-shell restart`; se um processo antigo encerrou o reinício junto com ele, use `rice-shell start`. Isso pode encerrar uma gravação de tela ativa.

Atalhos são calculados no carregamento da configuração Hyprland. A troca gerenciada faz os ajustes necessários; evite rodar várias shells por autostarts independentes. Não atualize o compositor isoladamente dos plugins/patches e do portal compatível.

## Primeira instalação / mudança do compositor

A ativação de NixOS não substitui o executável Hyprland já em execução. Para usar uma nova versão do compositor e seus patches, inicie uma sessão nova quando puder. Não carregue plugins de uma versão diferente no processo antigo.

O módulo usa a configuração Lua do Hyprland fixado pela flake; não foi feito para versões arbitrárias de Hyprland de outra distribuição. Teclas de brilho dependem de backlight ou DDC/CI suportado no monitor; desktops precisam de I²C/DDC habilitado. Nem todo monitor implementa controle de brilho por software.

## Finder / vidro

O Finder usa Nautilus/GTK e overlays de recursos. As transparências dependem também do compositor. O vidro GTK não é o mesmo shader de refração usado em painéis Quickshell. O botão amarelo decorativo pode aparecer sem minimizar: isso preserva a estética no ambiente tiling.

## Quick Look e Quickshot

Quick Look é o visualizador padrão de formatos compatíveis somente enquanto o perfil desta rice está ativo. O aplicativo de abertura externa anterior é preservado. Espaço/Esc/clique fora fecham a prévia. Alguns codecs dependem do backend Qt Multimedia/GStreamer e das capacidades da GPU.

Quickshot precisa do portal/captura funcionando na sessão Wayland. Screenshots pessoais e clipboard não são parte deste repositório. Não confunda build/testes unitários com comprovação visual em outro monitor/GPU.

## Atualizar

```sh
cd ~/quickintosh
git pull
```

Se usa o repositório como input remoto, atualize somente o input na flake do seu sistema e reconstrua. As fontes vendorizadas da shell não mudam com `nix flake update`: substituir o upstream exige revisar os integradores. O commit de origem é registrado em `upstream/SOURCES.json`.

## Ilha Dinâmica desaparecida ou vidro mostrando só o wallpaper

Verifique o estado real sem bloquear a tela:

```sh
quickintosh ipc call lock state
quickintosh ipc call rosa status
hyprctl -j locked
```

`nativeLocked` e `publishedLocked` devem coincidir. Houve uma regressão em que
o sinal Wayland era recebido antes de a propriedade nativa terminar de mudar:
a shell podia permanecer com `publishedLocked: true` após desbloquear. Isso
ocultava a ilha e podia manter a captura de janelas suspensa. A sincronização
agora é adiada até o fim desse ciclo de eventos e verificada periodicamente;
ela apenas observa o bloqueio nativo, nunca solicita desbloqueio.

Após um desbloqueio, `captureBlocked` pode permanecer ativo por 1,5 segundo
para estabilizar as capturas. Se o bloqueio nativo estiver ativo, autentique-se
normalmente; não encerre o locker para tentar contornar a senha. A opção de
ocultar a ilha em tela cheia e a ocultação por inatividade continuam válidas.

## Ícones da Central de Controle em escala fracionária

As máscaras intermediárias dos controles agora usam a densidade real da tela
e filtragem linear, preservando a suavização dos SVGs. Isso corrige a
serrilha reproduzida com escala de 150% e ampliação dos controles, sem substituir
os ícones ou mudar seus tamanhos. A renderização foi comparada em um Xvfb
isolado; drivers e aparência na máquina Arch de destino precisam ser conferidos
lá. Não force bibliotecas Qt de outra distribuição no ambiente do bundle.

## Desinstalar / voltar

Selecione outra shell pelo `rice-shell` antes de remover o módulo, para restaurar aparência e associações capturadas. Depois remova o import ou configure `quickintosh.enable = false` e faça rebuild. Seus arquivos de usuário não são apagados automaticamente. Restaure seus backups de Hyprland/scripts se quiser voltar à configuração anterior. Você também pode selecionar uma geração NixOS anterior no boot.
