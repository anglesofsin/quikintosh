# Discord na Dynamic Island

## O que cada modo detecta

A shell observa PipeWire para detectar chamadas básicas. Uma combinação Discord/WebRTC de entrada e saída pode indicar chamada mesmo sem companion; isso **não** informa nome do canal, avatar ou quem está falando.

Para a integração completa, o companion roda dentro do renderer do cliente já modificado e publica somente metadados de voz em `127.0.0.1:6891`. Não lê mensagens, não solicita token e não transmite áudio. O broker fica ativo com a ilha habilitada/desbloqueada. Não exponha a porta à rede.

Prioridade padrão: **Canary → PTB → Stable → Equibop**. Ajustável em Settings → Dynamic Island → Voice calls. Chamadas de DM e de servidor são suportadas. Streamer mode pode ocultar nomes/detalhes conforme suas preferências.

## NixOS: instalação declarativa recomendada

```nix
quickintosh.discord = {
  enable = true;
  clients = [ "canary" ]; # ou [ "canary" "ptb" "stable" ]
};
```

O módulo compila Equicord com o companion e instala os canais selecionados usando esse mod. Não instale simultaneamente outra variante do mesmo canal por outro módulo: remova o pacote duplicado ou adapte sua própria derivação. Se você usa plugins próprios/uma distribuição especial, prefira integrar o companion ao mod existente.

Depois do rebuild, **reinicie você mesmo o cliente** quando puder sair da chamada. Uma versão que já estava aberta continua executando o código antigo. A shell e os instaladores não derrubam sua chamada para forçar recarga.

## Equibop

Abra o Equibop uma vez para gerar a configuração e então execute:

```sh
quickintosh-discord-install
```

O instalador preserva o build escolhido, acrescenta o companion e usa `equicordDir` quando necessário. Ele requer o ASAR/configuração gerados pelo próprio Equibop. Reinicie o Equibop depois da instalação. Backups ficam em `~/.local/state/nixos-rice/voice-backup/`.

## Vencord / Equicord existentes em diretório gravável

Para um mod já instalado no seu home:

```sh
quickintosh-discord-install --renderer /caminho/do/seu/mod/renderer.js
```

Use o `renderer.js` real do mod, não um arquivo inventado nem arquivos de autenticação. O comando mantém backup e evita duplicar o companion. Para arquivos imutáveis em `/nix/store`, use a opção declarativa acima ou acrescente `modules/lickintosh/voice/discord-bridge.js` ao renderer no `postInstall` da sua derivação Nix.

## Discord gerenciado pelo Shade

O instalador reconhece clientes em execução em diretórios gerenciados `clients/.../resources`, preserva o bootstrap e inclui um hook Electron separado. Ele só modifica formatos reconhecidos. O empacotador ASAR do Shade precisa estar disponível em sua instalação habitual `~/Shade/ShadeSelfbot/node_modules/.pnpm`; formatos ou layouts diferentes exigem adaptação, não são sobrescritos às cegas.

Com esse Discord aberto:

```sh
quickintosh-discord-install
```

Reinicie depois, no momento que preferir. A integração não inclui Shade, seu código privado, chaves ou licenças; instale o cliente legitimamente por conta própria.

## Atualizações e limites

O guard verifica caminhos conhecidos a cada 30 segundos e pode reaplicar hooks substituídos por updates. Nunca reinicia o cliente. Reparos de bootstrap passam a valer na próxima inicialização; uma mudança nas APIs privadas do Discord ainda pode exigir atualização do companion. Não há garantia de compatibilidade eterna com updates de terceiros.

No modo externo básico, a ilha não inventa participantes, fotos ou botões funcionais. Quando chegam metadados completos do companion, eles têm prioridade.

## Testar sem interromper a chamada

```sh
quickintosh ipc call voice status
```

- `active: true`: chamada detectada.
- `external: true`: fallback PipeWire, sem metadados completos.
- `metadataClients`: clientes que publicaram metadados.
- `controls: true`: controles disponíveis para a sessão publicada.

Se aparecer apenas fallback, confirme qual executável/instalação do Discord você abriu; reinicie o cliente que recebeu o companion, habilite a integração nas Settings e confira Streamer mode. Se nada aparecer, confirme que o Discord usa PipeWire/PulseAudio da sessão e que a ilha não está desabilitada, bloqueada ou oculta em fullscreen.

Mais detalhes e testes: [README técnico da voz](../modules/lickintosh/voice/README.md).

## Chamadas recebidas na ilha

O companion publica o estado `incoming` para chamadas de DM/grupo que estão tocando para o usuário local. A ilha expande o cartão e oferece atender (verde) e recusar (vermelho) quando os métodos do cliente estão disponíveis. Clicar no restante do cartão recolhe a ilha sem rejeitar a chamada. O cancelamento pelo chamador limpa o cartão. Uma chamada recebida tem prioridade sobre outra chamada conectada.

Ative/desative a expansão em Settings → Dynamic Island → Voice calls → Expand incoming calls. Depois de instalar esta versão, reinicie o Discord manualmente quando puder interromper a chamada; o processo já aberto pode continuar com o companion antigo.

Outros aplicativos podem fornecer uma notificação com categoria `call.incoming` (ou `x-quickintosh.call.incoming`) e ações `accept`/`answer`/`call.accept` e `reject`/`decline`/`call.reject`. A ilha invoca as ações publicadas pelo próprio aplicativo; não simula cliques nem captura credenciais. Notificações comuns de mensagem não são tratadas como ligações. O app precisa encerrar a notificação ao cancelar/atender a chamada. Uma chamada atendida pode continuar sendo identificada pelo PipeWire quando o app publica streams ativos com `media.role=Communication`.

Não existe uma API universal Linux para atender chamadas em qualquer aplicativo: apps que não publicam o estado/ações precisam de um adaptador próprio. Navegadores que não expõem a função de comunicação no PipeWire não podem ser classificados como chamada apenas por usarem o microfone. Controles e participantes não são inventados no fallback.
