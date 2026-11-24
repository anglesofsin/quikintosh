# Wallpaper, cores e ícones

Coloque seus arquivos em `~/Pictures/Wallpapers`. Settings → Wallpaper seleciona o wallpaper; Appearance configura modo claro/escuro, accent, ícones, transparência e Liquid Glass. Menu Bar permite foreground automático/customizado e fundo opcional.

Os templates Matugen/Noctalia do setup original estão em `defaults/templates` e `defaults/theming.json`. Em uma instalação nova, o fallback empacotado fornece templates portáveis, sem exigir que você abra a Noctalia Legacy primeiro. Quando há configuração Legacy existente, suas seleções e templates próprios têm precedência.

Os destinos incluem Kitty, GTK, Qt, Zed, Telegram, Steam, Zen/Firefox, Neovim, Spicetify, OpenCode e OBS, conforme templates disponíveis. Um template não instala o aplicativo. Alguns programas exigem importar seu tema gerado ou habilitar temas personalizados; plugins e perfis específicos não são distribuídos como se pertencessem a todos os usuários. Os hooks específicos do perfil pessoal de desenvolvimento não foram exportados.

No Zen, o perfil é descoberto no home da pessoa que instala. Neovim/Spicetify/OBS precisam de suas configurações de tema para consumir os arquivos gerados. Você pode adaptar os destinos no catálogo ou usar `~/.config/noctalia-legacy/user-templates.toml`.

- Estado das aplicações: `~/.local/state/lickintosh/theming/status.json`
- Log: `~/.local/state/lickintosh/theming/apply.log`
- Ícones: bancos claros/escuros e renderizador tintado em `modules/lickintosh/layered-icons`.
- Preferências: `~/.config/lickintosh/shell-config.json` e Settings.

Não coloque API keys, perfis de navegador, conversas, contas Discord ou dados de clima pessoais nos presets versionados. A localização de clima deve ser escolhida no seu próprio Settings.
