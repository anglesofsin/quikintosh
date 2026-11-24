# Validação do suporte Arch

Esta implementação foi preparada no computador de desenvolvimento NixOS. Não foi instalada numa máquina Arch física e nenhuma sessão gráfica Arch foi iniciada durante estes testes.

Verificações realizadas:

- Build do bundle Arch (`.#arch`) e do wrapper Mesa (`.#arch-mesa`).
- Seis testes de ativação em home temporário: instalação isolada, restauração de backup, preservação de arquivo editado, reinstalação, rollback de falha e ambiente de execução.
- Ativação/desinstalação do bundle real em home temporário; conferência de ausência dos caminhos do desenvolvedor e caminhos de comandos NixOS na configuração gerada.
- Dois arquivos Lua reais da rice analisados com `luac -p` após a adaptação dos caminhos.
- Launchers gerados analisados com `bash -n`; fontes Python verificadas com `py_compile`.
- Dezoito testes existentes do roteador de atalhos/seletor de shells passaram após a adaptação do diretório de estado.

O teste não instalou pacotes com pacman, não escreveu PAM do host, não registrou sessão no display manager, não acionou bloqueio, screenshots, mouse ou teclado e não reiniciou o desktop do desenvolvedor.

Pendente no Arch de destino: inicialização gráfica real, driver Mesa/NVIDIA/híbrido, desbloqueio PAM, portal/compartilhamento, áudio, apps nativos iniciados pela shell e integração Discord do cliente que a pessoa usa. O checklist e os comandos de diagnóstico estão em [ARCH.md](ARCH.md). Build e testes de arquivos não substituem essa validação no hardware de destino.
