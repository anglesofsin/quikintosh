# Instalador Arch

Leia [o guia completo](../docs/ARCH.md) antes de executar.

```sh
sudo bash arch/system-setup.sh
./arch/install.sh doctor
./arch/install.sh install --graphics mesa
./arch/install.sh register-session
```

Para NVIDIA proprietário: `--graphics nvidia`. Os dois primeiros comandos têm funções diferentes: `system-setup.sh` prepara pacotes/PAM como root; `install.sh` deve rodar como usuário normal e instala um bundle Nix em uma sessão separada. O Arch não vira NixOS.

`install.sh uninstall` restaura os arquivos gerenciados intactos e preserva edições do usuário. O diretório `~/.config/hypr` existente não é substituído. Nada é iniciado automaticamente no desktop durante a instalação.

Scripts:

- `install.py`: diagnóstico, build, ativação com backup/rollback, entrada de login e remoção;
- `launcher.py`: ambiente, comandos públicos, drivers e ciclo da sessão/portal;
- `system-setup.sh`: pacman com prompts normais, daemon Nix e PAM do host.

Testes: `python3 tests/test_arch_installer.py`. Eles usam home temporário e não controlam a sessão gráfica real.
