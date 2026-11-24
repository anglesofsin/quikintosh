# Idioma e escala da Quickintosh

Em **Settings → General → Language & Region**, selecione **Português (Brasil)**.
O modo automático também reconhece localidades `pt_*`. O idioma é aplicado
sem reiniciar a sessão; os títulos e a busca dos Ajustes acompanham a seleção.
O idioma de aplicativos externos continua sob controle dos próprios aplicativos
e do sistema.

O catálogo inclui menus, ações, notificações, widgets, tela de bloqueio e opções
dos Ajustes. Textos técnicos e termos ainda sem tradução usam o equivalente
inglês; IDs de ações, caminhos, comandos, nomes de aplicativos e conteúdo de
notificações não são traduzidos. A Ilha Dinâmica acompanha a seleção da shell.

Em **Settings → Appearance → Interface Scale**, escolha entre **75% e 200%** e
clique em **Apply & Reload**. A escolha é salva no perfil da Quickintosh e a
interface é recarregada. Outros aplicativos, outras rices, resolução, taxa de
atualização e escala do compositor não são alterados. O padrão é 100%.

O ajuste usa a escala nativa do Qt, incluindo geometria e entrada dos controles,
em vez de esticar uma imagem pronta. A escala é multiplicada pela escala de
tela já configurada no compositor. Valores inválidos no arquivo de configuração
usam 100% como padrão seguro. O controle antigo de tamanho dos Ajustes em
Acessibilidade continua limitado àquela janela; não substitui a escala global.

Testes sem interação com a sessão: `tests/test_locale_scale_auth.py`. O teste
PAM real com políticas temporárias precisa de `QUICKINTOSH_TEST_PAM_LIBRARY`
apontando para a biblioteca Linux-PAM de teste e nunca modifica `/etc/pam.d`.
