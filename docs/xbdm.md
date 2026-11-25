# XBDM e UDP: manda o arquivo, pega o log

Pra fechar o ciclo, sobe o app, lê o log e confere o que aconteceu. Os comandos estão aqui; usa o diretório certo.

O devkit fornece **um cliente**, não o monitor do console. A preparação do console é externa à organização. XBDM não tem autenticação: use rede local confiável, sem exposição à internet. Esta tarefa de preparação não acessou console algum.

Instale com `python3 -m venv .venv` e `.venv/bin/pip install -e '.[screenshot]'`; ou use sem instalação com `PYTHONPATH=src python3 -m revive360.xbdm`. O extra `screenshot` só acrescenta Pillow para PNG.

```sh
xbdm --help
xbdm discover --network 192.168.1.0/24
xbdm ls 192.168.1.50 'HDD:\'
xbdm mkdir 192.168.1.50 'HDD:\Apps'
xbdm mkdir 192.168.1.50 'HDD:\Apps\Revive360Hello'
xbdm put 192.168.1.50 dist/hello/default.xex 'HDD:\Apps\Revive360Hello\default.xex'
xbdm get 192.168.1.50 'HDD:\Apps\Revive360Hello\default.log' console.log
xbdm run 192.168.1.50 'HDD:\Apps\Revive360Hello\default.xex'
```

Os IPs são exemplos. `discover` só varre a /24 ou rede menor informada, lê a saudação `201` e fecha; não manda linhas vazias. Não use `echo > /dev/tcp/.../730` nem na porta 21 para sondar o console: esse padrão foi associado a quedas nas sessões anteriores. Com BadUpdate, o XBDM pode aparecer e sumir durante o boot; espere a preparação do usuário terminar antes de transferir.

Use `HDD:` no protocolo XBDM, mesmo que outro programa mostre `Hdd1:`. O cliente converte esse alias para `HDD:`. Todo caminho precisa ser absoluto. `run` envia tanto `title="...default.xex"` como `directory="...\\"`, para os arquivos relativos serem encontrados. Comando enviado não prova que o app abriu: confira imagem e log. A CLI não oferece reboot, comando arbitrário ou `debugger connect`.

`sendfile` e `getfile` são transferências completas. Não há retomada por `writefile`, nem leitura parcial por `getfile offset/size`: o monitor observado ignora esses parâmetros. O cliente transmite em blocos de memória e só promove um download `.part` ao destino após terminar. Confirme tamanho/hash quando transferir material importante. Não sobrescreva arquivos de um título em execução; saia por B antes. `413` é erro, não sucesso. `414` pode significar caminho ausente ou acesso negado; confira a pasta-mãe. `mkdir` aceita somente `410` como “já existe”.

## Log sem debugger

```sh
xbdm log --bind 0.0.0.0 --port 7301 --output console-udp.log
```

Antes de abrir o app, coloque `net_log.txt` ao lado do XEX contendo `<IP-DO-PC> 7301`. O IP é o do receptor, não o do console. O arquivo não vai ao pacote público. Autorize essa porta UDP no firewall local conforme sua rede. Para PC, o arquivo fica no diretório de trabalho do processo. Cada datagrama começa com contador uint32 em ordem de rede, seguido da mensagem; lacunas podem ser perda, reordenação ou reinício do app. UDP é diagnóstico e não confirma entrega de todo o log.

O xsdk também escreve o log do título, normalmente `default.log` quando o pacote usa `default.xex`. Desligar o console pode perder o fim do cache de disco. Prefira UDP. `DbgPrint` exige `dbgprint.txt`; não é usado neste fluxo. Não abra um debugger para coletar texto: já houve laço de exceções que inutilizou o canal XBDM até uma intervenção física.

## Captura de tela

```sh
xbdm shot 192.168.1.50 capture
xbdm shot 192.168.1.50 capture --png
# Caso xsdk conhecido: somente a faixa superior, NÃO uma captura completa 720p:
xbdm shot 192.168.1.50 capture-top --png --width 1280 --height 256
```

Sempre ficam `.raw` e `.json`. Para o formato observado `0x18280186`, o PNG desfaz o tiling Xenos e a inversão 8in32 de ARGB. Outros formatos são recusados em vez de inventar uma imagem. O monitor pode anunciar 640×480 enquanto o framebuffer real do xsdk é 1280×720: o buffer recebido é parcial e a conversão pelo cabeçalho pode sair embaralhada. O override 1280×256 recuperou a faixa superior no console medido; não é uma correção universal nem substitui foto da TV. `screenshot` pode reduzir temporariamente o app a cerca de 5 fps; não use durante medição de desempenho.

Para travamento total, o XBDM pode morrer junto. Não tente `magicboot cold` nem `HalReturnToFirmware(1)`; reboot não restaura BadUpdate. Quem está ao lado do aparelho decide a recuperação física. Prefira cabo de rede para envios grandes.
