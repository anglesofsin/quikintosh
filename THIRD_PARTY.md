# Créditos e licenças

Quickintosh é um fork/integrador; não reivindica autoria dos projetos abaixo.

| Componente | Origem | Licença / avisos |
| --- | --- | --- |
| Shell e assets upstream | https://github.com/kelian-4/lickintosh | GPL-3.0-or-later para o código; veja LICENSE, THIRD_PARTY_LICENSES e avisos dos assets em upstream/lickintosh |
| Dynamic Island base | https://github.com/fedyaqq34356/rosa | GPL-3.0; licença copiada à derivação |
| Hyprland | https://github.com/hyprwm/Hyprland | BSD-3-Clause; patches locais em modules/ |
| Noctalia | https://github.com/noctalia-dev/noctalia | Licença do checkout fixado; não é re-licenciado aqui |
| Caelestia | https://github.com/caelestia-dots/shell | Licença do input fixado |
| eqSh | https://github.com/eq-desktop/eqsh | Licença do input fixado |
| Darling | https://github.com/darlinghq/darling/releases/tag/v0.1.20260608 | GPL-3.0-or-later e licenças de cada componente Darwin; avisos dos pacotes oficiais preservados na derivação |
| GTK Tahoe | https://github.com/vinceliuice/MacTahoe-gtk-theme | GPL-3.0; baixado pela receita Nix |
| Ícones adicionais | https://github.com/MiaowCham/macOS_Tahoe_Themes_for_MDF e https://github.com/Scrimas/MacOS-Like | Consulte licenças/avisos das fontes; assets não são re-licenciados pelo GPL do código |
| Quickshell, Nautilus, Matugen, Equicord e demais dependências | Inputs/Nixpkgs fixados em flake.lock | Cada dependência conserva sua licença |
| Ícones Lucide do Quickshot | modules/lickintosh/capture/assets | Lucide-LICENSE incluída |

A aparência do Quickshot foi inspirada em https://github.com/simmzl/quickshot. Quick Look segue o fluxo visual do macOS; não contém binários do QuickLook da Apple. Os assets/fonts herdados do upstream conservam os direitos e condições dos respectivos titulares; a licença deste código não concede direitos adicionais sobre marcas, fontes ou artes de terceiros.

As revisões exatas dos inputs estão em flake.lock; a shell vendorizada está identificada em upstream/SOURCES.json.
