# Perfil visual de 27/11/2026

Snapshot sanitizado dos controles visuais da sessão, separado dos padrões genéricos. Não é um backup da pasta pessoal. Não importa wallpapers, credenciais, histórico, conteúdo de widgets, servidores ou pareamentos.

Veja [o guia completo](../../docs/REPRODUCING.md). Prévia e aplicação explícita:

```sh
python3 scripts/visual-profile.py restore profiles/current-desktop/profile.json
python3 scripts/visual-profile.py restore profiles/current-desktop/profile.json --apply
```

As preferências JSON são mescladas; arquivos de texto do Kitty são substituídos com backup local. Isso não reinicia a shell nem os aplicativos. Use o ambiente Nix correspondente à mesma revisão para obter os shaders, plugins, fontes e assets necessários.
