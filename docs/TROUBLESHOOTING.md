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

## Desinstalar / voltar

Selecione outra shell pelo `rice-shell` antes de remover o módulo, para restaurar aparência e associações capturadas. Depois remova o import ou configure `quickintosh.enable = false` e faça rebuild. Seus arquivos de usuário não são apagados automaticamente. Restaure seus backups de Hyprland/scripts se quiser voltar à configuração anterior. Você também pode selecionar uma geração NixOS anterior no boot.
